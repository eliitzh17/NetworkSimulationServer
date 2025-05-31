import aio_pika
import json
from aiormq.exceptions import ChannelInvalidStateError
import traceback
import asyncio
from datetime import datetime, UTC
from typing import Optional, Any, Dict, Set
from app.utils.logger import LoggerManager
from app.app_container import app_container
from app.db.mongo_db_client import MongoDBConnectionManager

class BaseConsumer:
    def __init__(
        self, 
        db: MongoDBConnectionManager, 
        queue: aio_pika.Queue, 
        dead_letter_queue: Optional[aio_pika.Queue] = None,
        max_retries: int = 0,
        retry_delay: int = 0,
        max_concurrent_tasks: int = 0,
        message_timeout: int = 0,
    ):
        if max_concurrent_tasks < 0:
            raise ValueError("max_concurrent_tasks must be non-negative")
        if message_timeout <= 0:
            raise ValueError("message_timeout must be positive")
        if retry_delay <= 0:
            raise ValueError("retry_delay must be positive")
            
        self.logger = LoggerManager.get_logger(self.__class__.__name__)
        self.db = db
        self.queue = queue
        self.dead_letter_queue = dead_letter_queue
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.semaphore = asyncio.Semaphore(max_concurrent_tasks)
        self.message_timeout = message_timeout
        self.processing_tasks: Set[asyncio.Task] = set()

    async def start_consuming(self) -> None:
        self.logger.info(f" [*] Waiting for messages on {self.queue.name}. To exit press CTRL+C")
        await self.queue.consume(self.on_message)

    async def on_message(self, message: aio_pika.IncomingMessage) -> None:
        self.logger.info(f" [*] Received new message for {self.__class__.__name__}")
        
        async def sem_task() -> None:
            try:
                async with self.semaphore:
                    async with asyncio.timeout(self.message_timeout):
                        await self._process_message(message)
            except asyncio.TimeoutError:
                self.logger.error(f"Message processing timed out after {self.message_timeout} seconds")
                await self._handle_processing_error(
                    TimeoutError(f"Message processing timed out after {self.message_timeout} seconds"),
                    message,
                    self._get_retry_count(message)
                )
            except Exception as e:
                self.logger.error(f"Error in sem_task: {e}\n{traceback.format_exc()}")
                await self._handle_processing_error(e, message, self._get_retry_count(message))
            finally:
                self.processing_tasks.discard(task)

        task = asyncio.create_task(sem_task())
        self.processing_tasks.add(task)
        task.add_done_callback(self.processing_tasks.discard)

    async def _process_message(self, message: aio_pika.IncomingMessage):
        try:
            async with message.process():
                retry_count = self._get_retry_count(message)
                if self._exceeded_max_retries(retry_count):
                    self.logger.error(f"❌ Message exceeded maximum retry attempts ({self.max_retries})")
                    await self._move_to_dead_letter_queue(message)
                    return
                try:
                    await self.process_message(message)
                    self.logger.info(f"✅ Message processed successfully by {self.__class__.__name__}")
                except Exception as e:
                    await self._handle_processing_error(e, message, retry_count)
        except ChannelInvalidStateError as e:
            self.logger.error(f"{self.__class__.__name__}[!] ChannelInvalidStateError: {e}\n{traceback.format_exc()}")
            raise e
        except Exception as e:
            self.logger.error(f"{self.__class__.__name__} Error processing message: {e}\n{traceback.format_exc()}")
            raise e

    def _parse_message_body(self, message: aio_pika.IncomingMessage) -> Dict[str, Any]:
        try:
            return json.loads(message.body.decode())
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse message body: {e}")
            raise ValueError(f"Invalid message format: {e}")

    def _get_retry_count(self, message: aio_pika.IncomingMessage) -> int:
        return message.headers.get('x-retry-count', 0) if message.headers else 0

    def _exceeded_max_retries(self, retry_count: int) -> bool:
        return retry_count >= self.max_retries
    
    async def _handle_processing_error(self, error: Exception, message: aio_pika.IncomingMessage, retry_count: int):
        error_context = {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'retry_count': retry_count,
            'timestamp': datetime.now(UTC).isoformat()
        }
        self.logger.error(f"Error processing message: {error_context}")
        
        if self._exceeded_max_retries(retry_count + 1):
            self.logger.error(f"Exceeded max retries, moving message to dead letter queue.")
            await self._move_to_dead_letter_queue(message)
            return
        
        self.logger.warning(f"🔄 Retrying message to queue: {message.routing_key} (attempt {retry_count + 1}/{self.max_retries})")
        await self._republished_message_to_queue(message, retry_count, error_context)

    async def _move_to_dead_letter_queue(self, message: aio_pika.IncomingMessage):
        if self.dead_letter_queue:
            headers = dict(message.headers) if message.headers else {}
            headers['x-dlq-timestamp'] = datetime.now(UTC).isoformat()
            headers['x-dlq-reason'] = 'max_retries_exceeded'
            
            self.logger.info(f"Moving message to dead letter queue: {self.dead_letter_queue.name}")
            await self.dead_letter_queue.channel.default_exchange.publish(
                aio_pika.Message(
                    body=message.body,
                    headers=headers,
                    delivery_mode=message.delivery_mode,
                    content_type=message.content_type,
                ),
                routing_key=self.dead_letter_queue.name
            )
        else:
            self.logger.warning("Dead letter queue not configured. Message will be lost.")

    async def _republished_message_to_queue(self, message: aio_pika.IncomingMessage, retry_count: int, error_context: Dict[str, Any]):
        """Move a message to the retry queue with updated retry information.
        
        Args:
            message: The original message to retry
            retry_count: Current retry count
            error_context: Dictionary containing error information
        """

        delay = self.retry_delay * (2 ** retry_count)
        self.logger.info(f"Retrying in {delay} seconds (attempt {retry_count + 1}/{self.max_retries})")
        await asyncio.sleep(delay)
        headers = dict(message.headers) if message.headers else {}
        headers['x-retry-count'] = retry_count + 1
        headers['x-last-error'] = error_context
        headers['x-retry-timestamp'] = datetime.now(UTC).isoformat()
        
        self.logger.info(f"Re-publishing message to queue: {message.routing_key} (attempt {retry_count + 1}/{self.max_retries})")
        await self.queue.channel.default_exchange.publish(
            aio_pika.Message(
                body=message.body,
                headers=headers,
                delivery_mode=message.delivery_mode,
                content_type=message.content_type,
            ),
            routing_key=message.routing_key
        )

    async def process_message(self, message: aio_pika.IncomingMessage) -> None:
        raise NotImplementedError("Subclasses must implement process_message()")


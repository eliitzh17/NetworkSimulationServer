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
from motor.motor_asyncio import AsyncIOMotorClient
import random

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
        
        try:
            # Validate message before processing
            if not message.body:
                raise ValueError("Empty message body received")
                
            async with message.process():
                try:
                    async with asyncio.timeout(self.message_timeout):
                        await self.process_message(message)
                        self.logger.info(f"✅ Message processed successfully by {self.__class__.__name__}")
                except asyncio.TimeoutError as e:
                    self.logger.error("Message processing timed out")
                    await self._handle_processing_error(e, message, self._get_retry_count(message))
                except ValueError as ve:
                    self.logger.error(f"Message validation error: {str(ve)}")
                    await self._handle_processing_error(ve, message, self._get_retry_count(message))
                except Exception as e:
                    self.logger.error(f"Unexpected error during message processing: {str(e)}")
                    await self._handle_processing_error(e, message, self._get_retry_count(message))

        except ChannelInvalidStateError as e:
            self.logger.error(f"Channel error: {str(e)}")
            raise e
        except Exception as e:
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
            'timestamp': datetime.now(UTC).isoformat(),
            'traceback': traceback.format_exc() 
        }
        self.logger.error(f"Error processing message: {str(error)}")

        # Handle specific error types
        if isinstance(error, asyncio.TimeoutError):
            self.logger.error("Message processing timed out")
        elif isinstance(error, ValueError):
            self.logger.error("Message validation failed")
            # Don't retry validation errors
            await self._move_to_dead_letter_queue(message, error_context)
            return

        if self._exceeded_max_retries(retry_count):
            self.logger.error(f"❌ Message exceeded maximum retry attempts ({self.max_retries})")
            await self._move_to_dead_letter_queue(message, error_context)
            return
        
        # Calculate delay with jitter to prevent thundering herd
        base_delay = self.retry_delay * (2 ** retry_count)
        jitter = random.uniform(0, 0.1 * base_delay) 
        delay = base_delay + jitter
        
        self.logger.info(f"Waiting {delay:.2f} seconds before retry...")
        await asyncio.sleep(delay)

        headers = dict(message.headers) if message.headers else {}
        headers.update({
            'x-retry-count': retry_count + 1,
            'x-last-error': str(error),
            'x-last-error-time': datetime.now(UTC).isoformat(),
            'x-next-retry-delay': delay,
            'x-error-type': type(error).__name__
        })

        try:
            # Republish the message to the queue with updated headers
            await self.queue.channel.default_exchange.publish(
                aio_pika.Message(
                    body=message.body,
                    headers=headers,
                    delivery_mode=message.delivery_mode,
                    content_type=message.content_type,
                ),
                routing_key=self.queue.name
            )

            self.logger.warning(f"🔄 Message requeued (attempt {retry_count + 1}/{self.max_retries})")
        except Exception as e:
            self.logger.error(f"Failed to requeue message: {str(e)}")
            # If we can't requeue, move to DLQ
            await self._move_to_dead_letter_queue(message, {**error_context, 'requeue_failure': str(e)})

    async def _move_to_dead_letter_queue(self, message: aio_pika.IncomingMessage, error_context: Dict[str, Any]):
        if self.dead_letter_queue:
            headers = dict(message.headers) if message.headers else {}
            headers.update(error_context)
            headers['x-dlq-timestamp'] = datetime.now(UTC).isoformat()
            headers['x-dlq-reason'] = 'max_retries_exceeded'
            
            await self.dead_letter_queue.channel.default_exchange.publish(
                aio_pika.Message(
                    body=message.body,
                    headers=headers,
                    delivery_mode=message.delivery_mode,
                    content_type=message.content_type,
                ),
                routing_key=self.dead_letter_queue.name
            )
            self.logger.info(f"Message moved to DLQ: {self.dead_letter_queue.name}")
        else:
            self.logger.warning("⚠️ No DLQ configured, message will be lost")

    async def process_message(self, message: aio_pika.IncomingMessage) -> None:
        raise NotImplementedError("Subclasses must implement process_message()")


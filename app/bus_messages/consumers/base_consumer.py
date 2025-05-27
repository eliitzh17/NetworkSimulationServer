import aio_pika
import json
from aiormq.exceptions import ChannelInvalidStateError
import traceback
import asyncio
from datetime import datetime, UTC
from typing import Optional, Any, Dict
from app.utils.logger import LoggerManager
import time

class BaseConsumer:
    def __init__(
        self, 
        db, 
        queue: aio_pika.Queue, 
        logger_name: str, 
        retry_queue: Optional[aio_pika.Queue] = None, 
        dead_letter_queue: Optional[aio_pika.Queue] = None,
        max_retries: int = 3,
        retry_delay: int = 1,
        max_concurrent_tasks: int = 3,
    ):
        self.db = db
        self.queue = queue
        self.retry_queue = retry_queue or queue
        self.dead_letter_queue = dead_letter_queue
        self.logger = LoggerManager.get_logger(logger_name)
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.semaphore = asyncio.Semaphore(max_concurrent_tasks)

    async def start_consuming(self):
        self.logger.info(f" [*] Waiting for messages on {self.queue.name}. To exit press CTRL+C")
        await self.queue.consume(self.on_message)

    async def on_message(self, message: aio_pika.IncomingMessage):
        self.logger.info(f" [*] Received new message for {self.__class__.__name__}")
        # Process each message in its own task for parallelism, but limit concurrency with semaphore
        async def sem_task():
            async with self.semaphore:
                await self._process_message(message)
        task = asyncio.create_task(sem_task())
        # Optionally, track tasks if you want to await them later or handle errors
        # self.processing_tasks.add(task)
        # task.add_done_callback(self.processing_tasks.discard)

    async def _process_message(self, message: aio_pika.IncomingMessage):
        try:
            async with message.process():
                retry_count = self._get_retry_count(message)
                if self._exceeded_max_retries(retry_count):
                    self.logger.error(f"Message exceeded maximum retry attempts ({self.max_retries})")
                    await self._move_to_dead_letter_queue(message)
                    return
                try:
                    await self.process_message(message)
                    self.logger.info(f"✅ Message processed successfully by {self.__class__.__name__}")
                except Exception as e:
                    await self._handle_processing_error(e, message, retry_count)
        except ChannelInvalidStateError as e:
            self.logger.error(f"{self.__class__.__name__}[!] ChannelInvalidStateError: {e}\n{traceback.format_exc()}")
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
        
        delay = self.retry_delay * (2 ** retry_count)
        self.logger.info(f"Retrying in {delay} seconds (attempt {retry_count + 1}/{self.max_retries})")
        await asyncio.sleep(delay)
        
        headers = dict(message.headers) if message.headers else {}
        headers['x-retry-count'] = retry_count + 1
        headers['x-last-error'] = error_context
        
        if self._exceeded_max_retries(retry_count + 1):
            self.logger.error(f"Exceeded max retries, moving message to dead letter queue.")
            await self._move_to_dead_letter_queue(message)
            return
        await self.retry_queue.channel.default_exchange.publish(
            aio_pika.Message(
                body=message.body,
                headers=headers,
                delivery_mode=message.delivery_mode,
                content_type=message.content_type,
            ),
            routing_key= message.routing_key
        )

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

    async def process_message(self, message: aio_pika.IncomingMessage) -> None:
        raise NotImplementedError("Subclasses must implement process_message()")


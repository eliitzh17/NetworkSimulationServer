import os
import asyncio
from aio_pika import ExchangeType
from app.bus_messages.rabbit_mq_client import RabbitMQClient
from app.bus_messages.rabbit_mq_manager import RabbitMQManager
from app.utils.logger import LoggerManager
from app.app_container import app_container
from config import get_config

class BaseConsumerWorker:
    # Subclasses should override these
    LOGGER_NAME = None
    EXCHANGE_ENV = None
    EXCHANGE_TYPE = ExchangeType.DIRECT
    QUEUE_ENV = None
    CONSUMER_CLASS = None
    EXTRA_CONSUMER_KWARGS = None  # dict or None

    @classmethod
    def main(cls):
        asyncio.run(cls().setup_and_run())

    async def setup_and_run(self):
        logger = LoggerManager.get_logger(self.LOGGER_NAME)
        mongo_manager = app_container.mongo_manager()
        await mongo_manager.connect()
        db = getattr(mongo_manager, 'db', None)

        # RabbitMQ URL
        rabbitmq_url = app_container.config().RABBITMQ_URL
        rabbitmq_client = RabbitMQClient(rabbitmq_url)

        # Exchange name
        exchange_name = app_container.config().get(self.EXCHANGE_ENV)
        exchange_configs = [
            {"name": exchange_name, "type": self.EXCHANGE_TYPE, "durable": True},
        ]
        rabbitmq_manager = RabbitMQManager(rabbitmq_client, exchange_configs)
        await rabbitmq_manager.setup_exchanges()

        # Create a new channel for the consumer
        channel = await rabbitmq_manager.create_consumer_channel()
        main_queue, retry_queue, dead_letter_queue = await rabbitmq_manager.setup_queue_with_retry(
            queue_name=app_container.config().get(self.QUEUE_ENV),
            exchange_name=exchange_name,
            channel=channel
        )
        consumer_kwargs = dict(
            db=db,
            queue=main_queue,
            logger_name=f"{self.LOGGER_NAME}",
            retry_queue=retry_queue,
            dead_letter_queue=dead_letter_queue,
        )
        # Add config-based kwargs if present
        consumer_kwargs['max_retries'] = app_container.config().RABBITMQ_MAX_RETRIES
        consumer_kwargs['retry_delay'] = app_container.config().RABBITMQ_INITIAL_RETRY_DELAY
        if self.EXTRA_CONSUMER_KWARGS:
            consumer_kwargs.update(self.EXTRA_CONSUMER_KWARGS)
        consumer = self.CONSUMER_CLASS(**consumer_kwargs)
        await consumer.start_consuming()
        await asyncio.Future()  # Keep the worker alive 
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
    USE_CONFIG_FOR_RABBITMQ_URL = True
    USE_CONFIG_FOR_EXCHANGE = False
    USE_CONFIG_FOR_QUEUE = False
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
        if self.USE_CONFIG_FOR_RABBITMQ_URL:
            rabbitmq_url = app_container.config().RABBITMQ_URL
        else:
            rabbitmq_url = app_container.config().RABBITMQ_URL
        rabbitmq_client = RabbitMQClient(rabbitmq_url)

        # Exchange name
        if self.USE_CONFIG_FOR_EXCHANGE:
            exchange_name = getattr(app_container.config, self.EXCHANGE_ENV)
        else:
            exchange_name = app_container.config().EXCHANGE_ENV
        exchange_configs = [
            {"name": exchange_name, "type": self.EXCHANGE_TYPE, "durable": True},
        ]
        rabbitmq_manager = RabbitMQManager(rabbitmq_client, exchange_configs)
        await rabbitmq_manager.setup_exchanges()

        # Queue name
        if self.USE_CONFIG_FOR_QUEUE:
            queue_name = getattr(app_container.config, self.QUEUE_ENV)
        else:
            queue_name = app_container.config().QUEUE_ENV

        main_queue, retry_queue, dead_letter_queue = await rabbitmq_manager.setup_queue_with_retry(
            queue_name=queue_name,
            exchange_name=exchange_name
        )

        queues = {
            "main": main_queue,
            "retry": retry_queue,
            "dlq": dead_letter_queue
        }

        consumer_kwargs = dict(
            db=db,
            queue=main_queue,
            logger_name=self.LOGGER_NAME,
            retry_queue=retry_queue,
            dead_letter_queue=dead_letter_queue,
        )
        # Add config-based kwargs if present
        if hasattr(app_container.config, 'RABBITMQ_MAX_RETRIES'):
            consumer_kwargs['max_retries'] = getattr(app_container.config, 'RABBITMQ_MAX_RETRIES', None)
        if hasattr(app_container.config, 'RABBITMQ_INITIAL_RETRY_DELAY'):
            consumer_kwargs['retry_delay'] = getattr(app_container.config, 'RABBITMQ_INITIAL_RETRY_DELAY', None)
        if self.EXTRA_CONSUMER_KWARGS:
            consumer_kwargs.update(self.EXTRA_CONSUMER_KWARGS)

        consumer = self.CONSUMER_CLASS(**consumer_kwargs)
        await consumer.start_consuming()
        await asyncio.Future()  # Keep the worker alive 
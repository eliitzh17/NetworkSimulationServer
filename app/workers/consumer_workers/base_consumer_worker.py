import asyncio
from aio_pika import ExchangeType
from app.amps.rabbit_mq_client import RabbitMQClient
from app.amps.rabbit_mq_manager import RabbitMQManager
from app.utils.logger import LoggerManager
from app.app_container import app_container
from app.amps.consumers.base_consumer import BaseConsumer

class BaseConsumerWorker:
    
    def __init__(self, logger: str, exchange_key_name: str, 
                 exchange_type: ExchangeType, 
                 queue_key_name: str,
                 routing_key_pattern: str,
                 consumer_class: BaseConsumer):
        self.logger = LoggerManager.get_logger(logger)
        self.exchange_key_name = exchange_key_name
        self.exchange_type = exchange_type
        self.queue_key_name = queue_key_name
        self.routing_key_pattern = routing_key_pattern
        self.consumer_class = consumer_class

    @classmethod
    def main(cls):
        asyncio.run(cls().setup_and_run())

    async def setup_and_run(self):

        self.logger.info(f"Setting up {self.queue_key_name} consumer worker")
        
        # Mongo
        mongo_manager = app_container.mongo_manager()
        await mongo_manager.connect()

        # RabbitMQ
        rabbitmq_client = RabbitMQClient(app_container.config().RABBITMQ_URL)
        rabbitmq_manager = RabbitMQManager(rabbitmq_client)

        # Exchange name
        exchange_name = app_container.config().get(self.exchange_key_name)
        await rabbitmq_manager.setup_exchange(exchange_name, self.exchange_type, True)

        # Create a new channel for the consumer
        channel = await rabbitmq_manager.create_consumer_channel()

        # queues setup
        queue_name = app_container.config().get(self.queue_key_name)
        routing_key = self.routing_key_pattern if self.routing_key_pattern else queue_name
        dead_letter_queue = await rabbitmq_manager.setup_dlx_queue(channel, queue_name, exchange_name, routing_key)
        main_queue = await rabbitmq_manager.setup_queue(channel, queue_name, exchange_name, routing_key)

        consumer_kwargs = dict(
            db=mongo_manager.db,
            queue=main_queue,
            dead_letter_queue=dead_letter_queue,
        )

        consumer = self.consumer_class(**consumer_kwargs)

        self.logger.info(f"Starting '{queue_name}' consumer worker with '{self.routing_key_pattern}' as a routing key pattern")

        # Start consuming
        await consumer.start_consuming()
        await asyncio.Future()  # Keep the worker alive indefinitely
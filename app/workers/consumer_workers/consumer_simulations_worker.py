import os
import asyncio
from aio_pika import ExchangeType
from app.workers.consumer_workers.base_consumer_worker import BaseConsumerWorker
from app.bus_messages.consumers.base_consumer import BaseConsumer
from app.utils.logger import LoggerManager
from app.bus_messages.consumers.simulations_consumer import SimulationConsumer

class MultiQueueConsumerWorker(BaseConsumerWorker):
    LOGGER_NAME = "multi_queue_consumer"
    EXCHANGE_ENV = "SIMULATION_EXCHANGE"
    EXCHANGE_TYPE = ExchangeType.DIRECT
    USE_CONFIG_FOR_RABBITMQ_URL = True
    USE_CONFIG_FOR_EXCHANGE = False
    USE_CONFIG_FOR_QUEUE = False
    CONSUMER_CLASS = SimulationConsumer  # Replace with your actual consumer class

    # List of dicts, each dict configures a consumer for a queue
    CONSUMER_CONFIGS = [
         {
            'queue_env': 'NEW_SIMULATIONS_QUEUE',
            'max_retries': 3,
            'retry_delay': 2
        },
        {
            'queue_env': 'SIMULATIONS_UPDATE_QUEUE',
            'max_retries': 3,
            'retry_delay': 3
        },
        {
            'queue_env': 'SIMULATIONS_PAUSED_QUEUE',
            'max_retries': 3,
            'retry_delay': 1
        },
        {
            'queue_env': 'SIMULATIONS_RESUMED_QUEUE',
            'max_retries': 3,
            'retry_delay': 2
        },
        {
            'queue_env': 'SIMULATIONS_STOPPED_QUEUE',
            'max_retries': 3,
            'retry_delay': 2
        },
        {
            'queue_env': 'SIMULATIONS_COMPLETED_QUEUE',
            'max_retries': 5,
            'retry_delay': 5
        }
    ]

    async def setup_and_run(self):
        logger = LoggerManager.get_logger(self.LOGGER_NAME)
        from app.app_container import app_container
        mongo_manager = app_container.mongo_manager()
        await mongo_manager.connect()
        db = getattr(mongo_manager, 'db', None)

        # RabbitMQ URL
        if self.USE_CONFIG_FOR_RABBITMQ_URL:
            rabbitmq_url = app_container.config().RABBITMQ_URL
        else:
            rabbitmq_url = app_container.config().RABBITMQ_URL
        from app.bus_messages.rabbit_mq_client import RabbitMQClient
        rabbitmq_client = RabbitMQClient(rabbitmq_url)

        # Exchange name
        from app.bus_messages.rabbit_mq_manager import RabbitMQManager
        exchange_configs = [
            {"name": self.EXCHANGE_ENV, "type": self.EXCHANGE_TYPE, "durable": True},
        ]
        rabbitmq_manager = RabbitMQManager(rabbitmq_client, exchange_configs)
        await rabbitmq_manager.setup_exchanges()

        # Setup all consumers
        tasks = []
        for consumer_cfg in self.CONSUMER_CONFIGS:
            queue_name =consumer_cfg['queue_env']
            if queue_name is None:
                logger.error(f"Queue {consumer_cfg['queue_env']} not found")
                continue
            
            main_queue, retry_queue, dead_letter_queue = await rabbitmq_manager.setup_queue_with_retry(
                queue_name=queue_name,
                exchange_name=self.EXCHANGE_ENV
            )
            queues = {
                "main": main_queue,
                "retry": retry_queue,
                "dlq": dead_letter_queue
            }
            consumer_kwargs = dict(
                db=db,
                queue=main_queue,
                logger_name=f"{self.LOGGER_NAME}_{queue_name}",
                retry_queue=retry_queue,
                dead_letter_queue=dead_letter_queue,
                max_retries=consumer_cfg.get('max_retries', 3),
                retry_delay=consumer_cfg.get('retry_delay', 1),
            )
            if self.EXTRA_CONSUMER_KWARGS:
                consumer_kwargs.update(self.EXTRA_CONSUMER_KWARGS)
            consumer = self.CONSUMER_CLASS(**consumer_kwargs)
            tasks.append(asyncio.create_task(consumer.start_consuming()))
        await asyncio.gather(*tasks)
        await asyncio.Future()  # Keep the worker alive 
        
if __name__ == "__main__":
    asyncio.run(MultiQueueConsumerWorker.main()) 
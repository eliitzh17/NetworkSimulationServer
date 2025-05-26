from app.workers.consumer_workers.base_consumer_worker import BaseConsumerWorker
from app.bus_messages.consumers.run_links_consumer import LinksConsumer
from aio_pika import ExchangeType
import asyncio

class LinksConsumerWorker(BaseConsumerWorker):
    LOGGER_NAME = "links_consumer"
    EXCHANGE_ENV = "LINKS_EXCHANGE"
    EXCHANGE_TYPE = ExchangeType.DIRECT
    QUEUE_ENV = "RUN_LINKS_QUEUE"
    CONSUMER_CLASS = LinksConsumer
    USE_CONFIG_FOR_RABBITMQ_URL = False
    USE_CONFIG_FOR_EXCHANGE = False
    USE_CONFIG_FOR_QUEUE = False

if __name__ == "__main__":
    asyncio.run(LinksConsumerWorker.main()) 
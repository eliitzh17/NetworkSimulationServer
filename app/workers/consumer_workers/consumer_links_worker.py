from app.workers.consumer_workers.base_consumer_worker import BaseConsumerWorker
from app.messageBroker.consumers.run_links_consumer import LinksConsumer
from aio_pika import ExchangeType
import asyncio

class LinksConsumerWorker(BaseConsumerWorker):
    def __init__(self):
        super().__init__(
            logger="links_consumer",
            exchange_key_name="LINKS_EXCHANGE",
            exchange_type=ExchangeType.DIRECT,
            queue_key_name="RUN_LINKS_QUEUE",
            routing_key_pattern=None,
            consumer_class=LinksConsumer
    )

if __name__ == "__main__":
    asyncio.run(LinksConsumerWorker.main()) 
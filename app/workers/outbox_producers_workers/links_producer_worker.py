import os
import asyncio
from aio_pika import ExchangeType
from app.messageBroker.rabbit_mq_manager import RabbitMQManager
from app.messageBroker.producers.links_producer import LinksProducer
from app.workers.outbox_producers_workers.base_producer_worker import run_outbox_producer_worker
from app.app_container import app_container
from app.utils.logger import LoggerManager

def main():
    async def setup_and_run():
        logger = LoggerManager.get_logger("links_producer_worker")
        logger.info("Starting links producer worker")

        config = app_container.config()

        # get dependencies
        mongo_manager = app_container.mongo_manager()
        rabbitmq_client = app_container.rabbitmq_client()

        # connect to mongo
        await mongo_manager.connect()

        # setup rabbitmq
        rabbitmq_manager = RabbitMQManager(rabbitmq_client)
        await rabbitmq_manager.setup_exchange(config.LINKS_EXCHANGE, ExchangeType.DIRECT, True)

        # run the worker
        await run_outbox_producer_worker(
            logger,
            LinksProducer,
            producer_args={"rabbitmq_manager": rabbitmq_manager,
                            "exchange_name": config.LINKS_EXCHANGE,
                            "db": mongo_manager.db}
        )
    asyncio.run(setup_and_run())

if __name__ == "__main__":
    asyncio.run(main())  
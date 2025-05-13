from app.rabbit_mq.consumers.base_consumer import BaseConsumer
from app.rabbit_mq.rabbit_mq_client import RabbitMQClient
from aio_pika import ExchangeType
from app.core.link_bl import LinkBusinessLogic
from app.db.mongo_db_client import MongoDBConnectionManager
from app.utils.logger import LoggerManager
import asyncio
import os
from config import get_config
from app.models.simulation_models import Link
import json

class LinksConsumer(BaseConsumer):
    def __init__(self, db, rabbit_mq_client: RabbitMQClient, logger: LoggerManager):
        super().__init__(db, rabbit_mq_client, logger, os.getenv("LINKS_EXCHANGE"), os.getenv("LINKS_QUEUE"), ExchangeType.FANOUT)
        self.name = "links_consumer"

    async def process_message(self, data):
        try:
            self.logger.info(f"[i] Received link message: {data}")
            link_bl = LinkBusinessLogic(self.db)
        
            link_obj = Link(**json.loads(json.dumps(data.get('link'))))
            await link_bl.run_link(data.get('sim_id'), link_obj)
            self.logger.info(f"[i] Link for simulation {data.get('sim_id')} done ✅")
        except Exception as e:
            self.logger.error(f"{self.__class__.__name__}[!] Error processing message: {e}", exc_info=True)
            raise e

async def main():
    config = get_config()

    logger = LoggerManager.get_logger('links_consumer')
    logger.info("Starting links consumer")
    mongo_manager = MongoDBConnectionManager()
    await mongo_manager.connect()
    db = mongo_manager.db
    rabbit_mq_client = RabbitMQClient(config.RABBITMQ_URL)
    consumer = LinksConsumer(db, rabbit_mq_client, logger)
    connection = await consumer.start()
    try:
        await asyncio.Future()  # Keep running
    finally:
        await connection.close()
        await mongo_manager.close()

if __name__ == "__main__":
    asyncio.run(main()) 
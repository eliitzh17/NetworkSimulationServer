from app.rabbit_mq.consumers.base_consumer import BaseConsumer
from app.rabbit_mq.rabbit_mq_client import RabbitMQClient
from aio_pika import ExchangeType
import asyncio
from app.core.simulation_bl import SimulationBusinessLogic
from app.db.mongo_db_client import MongoDBConnectionManager
from app.utils.logger import LoggerManager
import os
from config import get_config


class SimulationConsumer(BaseConsumer):
    def __init__(self, db, rabbit_mq_client: RabbitMQClient, logger: LoggerManager):
        super().__init__(db, rabbit_mq_client, logger, os.getenv("SIMULATION_EXCHANGE"), os.getenv("SIMULATION_QUEUE"), ExchangeType.FANOUT)
        self.name = "simulations_consumer"

    async def process_message(self, data):
        try:
            self.logger.info(f"[*] Received message: {data}")
            simulation_manager = SimulationBusinessLogic(self.db)
            sim_id = data.get("sim_id")
            if sim_id:
                await simulation_manager.run_simulation(sim_id)
                self.logger.info(f"[*] Simulation {sim_id} done ✅")
            else:
                self.logger.info(f"[!] Received message without sim_id: {data}")
        except Exception as e:
            self.logger.error(f"{self.__class__.__name__}[!] Error processing message: {e}", exc_info=True)
            raise e

async def main():
    config = get_config()

    logger = LoggerManager.get_logger('simulations_consumer')
    logger.info("Starting simulations consumer")
    mongo_manager = MongoDBConnectionManager()
    await mongo_manager.connect()
    db = mongo_manager.db
    rabbit_mq_client = RabbitMQClient(config.RABBITMQ_URL)
    consumer = SimulationConsumer(db, rabbit_mq_client, logger)
    connection = await consumer.start()
    try:
        await asyncio.Future()  # Keep running
    finally:
        await connection.close()
        await mongo_manager.close()

if __name__ == "__main__":
    asyncio.run(main()) 
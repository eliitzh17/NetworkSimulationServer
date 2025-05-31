import asyncio
from aio_pika import ExchangeType
from app.amps.rabbit_mq_manager import RabbitMQManager
from app.amps.publishers.simulation_completed_publisher import SimulationCompletedPublisher
from app.workers.base_worker import run_outbox_publisher_worker
from app.app_container import app_container
from app.utils.logger import LoggerManager

def main():
    async def setup_and_run():

        logger = LoggerManager.get_logger("simulation_completed_publisher")  
        logger.info("Starting simulation completed publisher worker")
        
        # get dependencies
        mongo_manager = app_container.mongo_manager()
        rabbitmq_client = app_container.rabbitmq_client()
        
        # connect to mongo
        await mongo_manager.connect()

        # setup rabbitmq
        rabbitmq_manager = RabbitMQManager(rabbitmq_client)
        await rabbitmq_manager.setup_exchange(app_container.config().SIMULATION_EXCHANGE, ExchangeType.TOPIC, True)
        
        # run the worker
        await run_outbox_publisher_worker(
            SimulationCompletedPublisher,
            publisher_args={"rabbitmq_manager": rabbitmq_manager, 
                            "exchange_name": app_container.config().SIMULATION_EXCHANGE, 
                            "db": mongo_manager.db}
        )
    asyncio.run(setup_and_run())

if __name__ == "__main__":
    asyncio.run(main()) 
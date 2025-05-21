from app.rabbit_mq.consumers.base_consumer import BaseConsumer
from app.rabbit_mq.rabbit_mq_client import RabbitMQClient
from aio_pika import ExchangeType
from app.core.simulation_bl import SimulationBusinessLogic
from app.utils.logger import LoggerManager
import os


class SimulationConsumer(BaseConsumer):
    def __init__(self, db, rabbit_mq_client: RabbitMQClient, logger: LoggerManager):
        super().__init__(db, rabbit_mq_client, logger, os.getenv("SIMULATION_EXCHANGE"), os.getenv("SIMULATION_QUEUE"), ExchangeType.FANOUT)
        self.name = "simulations_consumer"

    #TODO: you can receive the object it self
    async def process_message(self, message):
        data = self._parse_message_body(message)
        simulation_manager = SimulationBusinessLogic(self.db, self.rabbit_mq_client)
        sim_id = data.get("sim_id")
        if sim_id:
            await simulation_manager.run_simulation(sim_id)
        else:
            self.logger.error(f"[!] Received message without sim_id: {data}")
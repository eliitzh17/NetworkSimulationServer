from app.rabbit_mq.rabbit_mq_client import RabbitMQClient
from app.models.simulation_models import Simulation
from typing import List
from app.rabbit_mq.publishers.base_publisher import BasePublisher
import os

class SimulationsPublisher(BasePublisher):
    def __init__(self, rabbit_mq_client: RabbitMQClient):
        super().__init__(rabbit_mq_client, 'simulation_publisher', os.getenv('SIMULATION_EXCHANGE'))

    def _serialize(self, obj: Simulation):
        return obj.model_dump()

    async def publish_simulations_messages(self, simulation_body: List[Simulation]):
        await self._publish_messages(simulation_body,"new_simulations")

    async def publish_simulation_completed_message(self, simulation_id: str):
        await self._publish_messages([simulation_id],"simulations_completed")
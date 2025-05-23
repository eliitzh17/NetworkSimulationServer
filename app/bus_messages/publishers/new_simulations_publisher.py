from app.bus_messages.publishers.base_publisher import BasePublisher
from app.models.statuses_enums import EventType
import os

class NewSimulationsPublisher(BasePublisher):
    def __init__(self, db, rabbitmq_manager, exchange_name):
        super().__init__(rabbitmq_manager, 'simulation_publisher', exchange_name, db)
        
    async def run_outbox_publisher(self):
        await super().run_outbox_publisher(EventType.SIMULATION_CREATED, os.getenv("NEW_SIMULATIONS_QUEUE"))
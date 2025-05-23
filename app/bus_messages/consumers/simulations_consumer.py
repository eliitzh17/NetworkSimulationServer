from app.bus_messages.consumers.base_consumer import BaseConsumer
from app.business_logic.topolgies_simulation_bl import TopologiesSimulationsBusinessLogic
from app.models.events_models import SimulationEvent
import aio_pika
import json

class SimulationConsumer(BaseConsumer):
    def __init__(self, db, queue, logger_name, retry_queue=None, dead_letter_queue=None, max_retries=3, retry_delay=1, monitor=None):
        super().__init__(db, queue, logger_name, retry_queue=retry_queue, dead_letter_queue=dead_letter_queue, max_retries=max_retries, retry_delay=retry_delay, monitor=monitor)
        self.name = "simulations_consumer"
        self.simulation_manager = TopologiesSimulationsBusinessLogic(db)

    async def process_message(self, message: aio_pika.IncomingMessage):
        data = json.loads(message.body.decode())
        simulation_event = SimulationEvent(**data)
        await self.simulation_manager.run_simulation(simulation_event)

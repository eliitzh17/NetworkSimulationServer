from app.bus_messages.consumers.base_consumer import BaseConsumer
from app.business_logic.topolgies_simulation_bl import TopologiesSimulationsBusinessLogic
from app.models.events_models import SimulationEvent

class SimulationCompletedConsumer(BaseConsumer):
    def __init__(self, db, queue, logger_name, retry_queue=None, dead_letter_queue=None, max_retries=3, retry_delay=1, monitor=None):
        super().__init__(db, queue, logger_name, retry_queue=retry_queue, dead_letter_queue=dead_letter_queue, max_retries=max_retries, retry_delay=retry_delay, monitor=monitor)
        self.name = "simulation_completed_consumer"
        self.simulation_manager = TopologiesSimulationsBusinessLogic(db)

    async def process_message(self, simulation_event: SimulationEvent):
        try:
            await self.simulation_manager.end_simulation(simulation_event)
        except Exception as e:
            self.logger.error(f"Error during simulation: {e}")
            raise e

from app.amps.consumers.base_consumer import BaseConsumer
from app.business_logic.topologies_simulation_bl import TopologiesSimulationsBusinessLogic
from app.models.events_models import SimulationEvent
import aio_pika
import json
from app.models.statuses_enums import EventType
from app.app_container import app_container

class SimulationConsumer(BaseConsumer):
    def __init__(self, db, 
                 queue,
                 dead_letter_queue=None):
        super().__init__(db, queue, 
                         dead_letter_queue=dead_letter_queue, 
                         max_retries=app_container.config().MAX_RETRIES, 
                         retry_delay=app_container.config().RETRY_DELAY,
                         max_concurrent_tasks=app_container.config().SIMULATIONS_CONSUMER_MAX_CONCURRENT_TASKS,
                         message_timeout=app_container.config().MESSAGE_TIMEOUT)
        self.simulation_manager = TopologiesSimulationsBusinessLogic(db)

    async def process_message(self, message: aio_pika.IncomingMessage):
        data = json.loads(message.body.decode())
        simulation_event = SimulationEvent(**data)
        match simulation_event.event_type:
            case EventType.SIMULATION_CREATED:
                await self.simulation_manager.run_simulation(simulation_event)
            case EventType.SIMULATION_UPDATED:
                pass
            case EventType.SIMULATION_PAUSED:
                await self.simulation_manager.pause_simulation(simulation_event)
            case EventType.SIMULATION_RESUMED:
                await self.simulation_manager.resume_simulation(simulation_event)
            case EventType.SIMULATION_STOPPED:
                pass
            case EventType.SIMULATION_COMPLETED:
                await self.simulation_manager.update_simulation_completed_status(simulation_event)

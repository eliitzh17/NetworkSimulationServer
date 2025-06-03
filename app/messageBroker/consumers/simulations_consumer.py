from app.messageBroker.consumers.base_consumer import BaseConsumer
from app.business_logic.topologies_simulation_bl import TopologiesSimulationsBusinessLogic
from app.models.events_models import SimulationEvent
import aio_pika
import json
from app.models.statuses_enums import EventType
from app.app_container import app_container
from app.db.events_db import EventsDB

class SimulationConsumer(BaseConsumer):
    def __init__(self, 
                 db, 
                 queue,
                 dead_letter_queue=None):
        self.config = app_container.config()
        super().__init__(db, queue, 
                         dead_letter_queue=dead_letter_queue, 
                         max_retries=self.config.MAX_RETRIES, 
                         retry_delay=self.config.RETRY_DELAY,
                         max_concurrent_tasks=self.config.SIMULATIONS_CONSUMER_MAX_CONCURRENT_TASKS,
                         message_timeout=self.config.MESSAGE_TIMEOUT)
        self.simulation_manager = TopologiesSimulationsBusinessLogic(db)
        self.events_db = EventsDB(db)

    async def process_message(self, message: aio_pika.IncomingMessage):
        data = json.loads(message.body.decode())
        simulation_event = SimulationEvent(**data)
        
        async with await self.db.client.start_session() as session:
            async with session.start_transaction():
                try:
                    match simulation_event.event_type:
                        case EventType.SIMULATION_CREATED:
                            await self.simulation_manager.run_simulation(simulation_event, session)
                        case EventType.SIMULATION_UPDATED:
                            pass
                        case EventType.SIMULATION_STOPPED:
                            pass
                        case EventType.SIMULATION_COMPLETED:
                            await self.simulation_manager.update_simulation_completed_status(simulation_event, session)
                        
                except Exception as e:
                    await session.abort_transaction()
                    raise e

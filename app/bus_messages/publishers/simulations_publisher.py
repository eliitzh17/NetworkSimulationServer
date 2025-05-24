from app.bus_messages.publishers.base_publisher import BasePublisher
from app.models.statuses_enums import EventType
import os
from app.models.message_bus_models import OutboxPublisher, EventTypeToRoutingKey

class SimulationsPublisher(BasePublisher):
    def __init__(self, db, rabbitmq_manager, exchange_name):
        super().__init__(rabbitmq_manager, 'simulation_publisher', exchange_name, db)
        
    async def run_outbox_publisher(self):
        self.outbox_publisher = OutboxPublisher(
            event_type_to_routing_key=[
                        EventTypeToRoutingKey(event_type=EventType.SIMULATION_CREATED, routing_key=os.getenv("NEW_SIMULATIONS_QUEUE")),
                        EventTypeToRoutingKey(event_type=EventType.SIMULATION_UPDATED, routing_key=os.getenv("SIMULATIONS_UPDATE_QUEUE")), 
                        EventTypeToRoutingKey(event_type=EventType.SIMULATION_PAUSED, routing_key=os.getenv("SIMULATIONS_PAUSED_QUEUE")), 
                        EventTypeToRoutingKey(event_type=EventType.SIMULATION_RESUMED, routing_key=os.getenv("SIMULATIONS_RESUMED_QUEUE")), 
                        EventTypeToRoutingKey(event_type=EventType.SIMULATION_STOPPED, routing_key=os.getenv("SIMULATIONS_STOPPED_QUEUE")), 
                        EventTypeToRoutingKey(event_type=EventType.SIMULATION_COMPLETED, routing_key=os.getenv("SIMULATIONS_COMPLETED_QUEUE"))],
            max_parallel=int(os.getenv("MAX_SIMULATIONS_IN_PARALLEL", 5)),
            initial_delay=int(os.getenv("INITIAL_DELAY", 1)),
            max_retries=int(os.getenv("MAX_RETRIES", 3)),
            retry_delay=int(os.getenv("RETRY_DELAY", 10))
        )
            
        await super().run_outbox_publisher()
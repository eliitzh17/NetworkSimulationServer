from app.bus_messages.publishers.base_publisher import BasePublisher
from app.models.statuses_enums import EventType
import os
from app.models.message_bus_models import OutboxPublisher, EventTypeToRoutingKey
from app.app_container import app_container
    
class SimulationsPublisher(BasePublisher):
    def __init__(self, db, rabbitmq_manager, exchange_name):
        super().__init__(rabbitmq_manager, 'simulation_publisher', exchange_name, db)
        
    async def run_outbox_publisher(self):
        self.outbox_publisher = OutboxPublisher(
            event_type_to_routing_key=[
                        EventTypeToRoutingKey(event_type=EventType.SIMULATION_CREATED, routing_key=app_container.config().NEW_SIMULATIONS_QUEUE),
                        EventTypeToRoutingKey(event_type=EventType.SIMULATION_UPDATED, routing_key=app_container.config().SIMULATIONS_UPDATE_QUEUE), 
                        EventTypeToRoutingKey(event_type=EventType.SIMULATION_PAUSED, routing_key=app_container.config().SIMULATIONS_PAUSED_QUEUE), 
                        EventTypeToRoutingKey(event_type=EventType.SIMULATION_RESUMED, routing_key=app_container.config().SIMULATIONS_RESUMED_QUEUE), 
                        EventTypeToRoutingKey(event_type=EventType.SIMULATION_STOPPED, routing_key=app_container.config().SIMULATIONS_STOPPED_QUEUE), 
                        EventTypeToRoutingKey(event_type=EventType.SIMULATION_COMPLETED, routing_key=app_container.config().SIMULATIONS_COMPLETED_QUEUE)],
            max_parallel=int(app_container.config().MAX_SIMULATIONS_IN_PARALLEL),
            initial_delay=int(app_container.config().INITIAL_DELAY),
            max_retries=int(app_container.config().MAX_RETRIES),
            retry_delay=int(app_container.config().RETRY_DELAY)
        )
            
        await super().run_outbox_publisher()
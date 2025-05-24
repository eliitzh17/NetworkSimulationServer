from app.bus_messages.publishers.base_publisher import BasePublisher
from app.models.statuses_enums import EventType
import os
from app.models.message_bus_models import OutboxPublisher, EventTypeToRoutingKey
class LinksPublisher(BasePublisher):
    def __init__(self, db, rabbitmq_manager, exchange_name):
        super().__init__(rabbitmq_manager, 'links_publisher', exchange_name, db)
    
    async def run_outbox_publisher(self):
        self.outbox_publisher = OutboxPublisher(
            event_type_to_routing_key=[EventTypeToRoutingKey(event_type=EventType.LINK_RUN, routing_key=os.getenv("RUN_LINKS_QUEUE"))],
            max_parallel=int(os.getenv("MAX_SIMULATIONS_IN_PARALLEL", 5)),
            initial_delay=int(os.getenv("INITIAL_DELAY", 1)),
            max_retries=int(os.getenv("MAX_RETRIES", 3)),
            retry_delay=int(os.getenv("RETRY_DELAY", 10))
        )
        await super().run_outbox_publisher()
        

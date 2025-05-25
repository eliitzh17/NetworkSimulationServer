from app.bus_messages.publishers.base_publisher import BasePublisher
from app.models.statuses_enums import EventType
import os
from app.models.message_bus_models import OutboxPublisher, EventTypeToRoutingKey
from app.app_container import app_container

class LinksPublisher(BasePublisher):
    def __init__(self, db, rabbitmq_manager, exchange_name):
        super().__init__(rabbitmq_manager, 'links_publisher', exchange_name, db)
    
    async def run_outbox_publisher(self):
        self.outbox_publisher = OutboxPublisher(
            event_type_to_routing_key=[EventTypeToRoutingKey(event_type=EventType.LINK_RUN, routing_key=app_container.config().RUN_LINKS_QUEUE)],
            max_parallel=int(app_container.config().MAX_SIMULATIONS_IN_PARALLEL),
            initial_delay=int(app_container.config().INITIAL_DELAY),
            max_retries=int(app_container.config().MAX_RETRIES),
            retry_delay=int(app_container.config().RETRY_DELAY)
        )
        await super().run_outbox_publisher()
        

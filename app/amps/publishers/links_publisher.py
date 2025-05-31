from app.amps.publishers.base_publisher import BasePublisher
from app.models.statuses_enums import EventType
import os
from app.models.message_bus_models import OutboxPublisher, EventTypeToRoutingKey
from app.app_container import app_container

class LinksPublisher(BasePublisher):
    def __init__(self, db, rabbitmq_manager, exchange_name):
        super().__init__(rabbitmq_manager, exchange_name, db, app_container.config().RUN_LINKS_QUEUE)
    
    async def run_outbox_publisher(self):
        self.outbox_publisher = OutboxPublisher(
            event_type_to_routing_key=[EventTypeToRoutingKey(event_type=EventType.LINK_RUN, routing_key=app_container.config().RUN_LINKS_QUEUE)],
            max_parallel=app_container.config().MAX_LINKS_IN_PARALLEL_PUBLISHER,
            initial_delay=app_container.config().INITIAL_DELAY,
            max_retries=app_container.config().MAX_RETRIES,
            retry_delay=app_container.config().RETRY_DELAY
        )
        await super().run_outbox_publisher()
        

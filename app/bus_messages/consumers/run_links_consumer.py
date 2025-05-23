from app.bus_messages.consumers.base_consumer import BaseConsumer
from app.business_logic.link_bl import LinkBusinessLogic  
from app.models.events_models import LinkEvent
import aio_pika
import json
class LinksConsumer(BaseConsumer):
    def __init__(self, db, queue, logger_name, retry_queue=None, dead_letter_queue=None, max_retries=3, retry_delay=1, monitor=None):
        super().__init__(db, queue, logger_name, retry_queue=retry_queue, dead_letter_queue=dead_letter_queue, max_retries=max_retries, retry_delay=retry_delay, monitor=monitor)
        self.link_bl = LinkBusinessLogic(db)
        self.name = "links_consumer"

    async def process_message(self, message: aio_pika.IncomingMessage):
        data = json.loads(message.body.decode())
        link_event = LinkEvent(**data)
        await self.link_bl.run_link(link_event)
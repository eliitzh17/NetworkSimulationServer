from app.amps.consumers.base_consumer import BaseConsumer
from app.business_logic.link_bl import LinkBusinessLogic  
from app.models.events_models import LinkEvent
import aio_pika
import json
from app.app_container import app_container

class LinksConsumer(BaseConsumer):
    def __init__(self, db, 
                 queue,
                 dead_letter_queue=None):
        super().__init__(db, queue, 
                         dead_letter_queue=dead_letter_queue, 
                         max_retries=app_container.config().MAX_RETRIES, 
                         retry_delay=app_container.config().RETRY_DELAY, 
                         max_concurrent_tasks=app_container.config().LINKS_CONSUMER_MAX_CONCURRENT_TASKS,
                         message_timeout=app_container.config().MESSAGE_TIMEOUT)
        self.link_bl = LinkBusinessLogic(db)

    async def process_message(self, message: aio_pika.IncomingMessage):

        is_last_retry =  self._get_retry_count(message) >= self.max_retries
        data = json.loads(message.body.decode())
        link_event = LinkEvent(**data)
        await self.link_bl.run_link(link_event,is_last_retry)
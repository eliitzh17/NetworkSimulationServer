from app.messageBroker.consumers.base_consumer import BaseConsumer
from app.business_logic.link_bl import LinkBusinessLogic  
from app.models.events_models import LinkEvent
import aio_pika
import json
from app.app_container import app_container

class LinksConsumer(BaseConsumer):
    def __init__(self, db, 
                 queue,
                 dead_letter_queue=None):
        self.config = app_container.config()
        super().__init__(db, queue, 
                         dead_letter_queue=dead_letter_queue, 
                         max_retries=self.config.MAX_RETRIES, 
                         retry_delay=self.config.RETRY_DELAY, 
                         max_concurrent_tasks=self.config.LINKS_CONSUMER_MAX_CONCURRENT_TASKS,
                         message_timeout=self.config.MESSAGE_TIMEOUT)
        self.link_bl = LinkBusinessLogic(db)

    async def process_message(self, message: aio_pika.IncomingMessage):
        is_last_retry =  self._get_retry_count(message) >= self.max_retries
        data = json.loads(message.body.decode())
        link_event = LinkEvent(**data)
        self.logger.info(f"Processing event: {link_event.event_id}")
        await self.link_bl.run_link(link_event,is_last_retry)
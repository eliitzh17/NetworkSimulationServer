from app.rabbit_mq.consumers.base_consumer import BaseConsumer
from app.rabbit_mq.rabbit_mq_client import RabbitMQClient
from aio_pika import ExchangeType
from app.core.link_bl import LinkBusinessLogic
from app.utils.logger import LoggerManager
import os
from app.models.topolgy_simulation_models import Link
import json

class LinksConsumer(BaseConsumer):
    def __init__(self, db, rabbit_mq_client: RabbitMQClient, logger: LoggerManager):
        super().__init__(db, rabbit_mq_client, logger, os.getenv("LINKS_EXCHANGE"), os.getenv("RUN_LINKS_QUEUE"), ExchangeType.FANOUT)
        self.name = "links_consumer"
    
    def is_last_try(self, message):
        return self._get_retry_count(message) == (self.max_retries - 1) 

    async def process_message(self, message):
        data = self._parse_message_body(message)
        link_bl = LinkBusinessLogic(self.db)
        sim_id = data.get('sim_id')
        link_obj = Link(**json.loads(json.dumps(data.get('link'))))
        await link_bl.run_link(sim_id, link_obj, self.is_last_try(message))
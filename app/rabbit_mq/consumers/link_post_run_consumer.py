from app.rabbit_mq.consumers.base_consumer import BaseConsumer
from app.rabbit_mq.rabbit_mq_client import RabbitMQClient
from app.utils.logger import LoggerManager
import os
from aio_pika import ExchangeType
from app.core.link_bl import LinkBusinessLogic

class LinkPostRunConsumer(BaseConsumer):
    def __init__(self, db, rabbit_mq_client: RabbitMQClient, logger: LoggerManager):
        super().__init__(db, rabbit_mq_client, logger, os.getenv("POST_LINK_EXCHANGE"), os.getenv("POST_LINK_QUEUE"), ExchangeType.FANOUT)
        self.name = "link_post_run_consumer"

    async def process_message(self, message):
        data = self._parse_message_body(message)
        link_bl = LinkBusinessLogic(self.db)
        await link_bl.post_link_execution_actions(data.get('simulation_id'), data.get('is_failed'))
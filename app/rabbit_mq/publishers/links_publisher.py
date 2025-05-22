from app.rabbit_mq.rabbit_mq_client import RabbitMQClient
from app.models.topolgy_models import Link
from typing import List
from app.rabbit_mq.publishers.base_publisher import BasePublisher
import os
class LinksPublisher(BasePublisher):
    def __init__(self, rabbit_mq_client: RabbitMQClient):
        super().__init__(rabbit_mq_client, 'links_publisher', os.getenv('LINKS_EXCHANGE'))

    def _serialize(self, obj):
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        return obj  # fallback for str, dict, etc.

    async def publish_run_links_messages(self, links_body: List[Link]):
        await self._publish_messages(links_body,os.getenv("RUN_LINKS_QUEUE"))
        

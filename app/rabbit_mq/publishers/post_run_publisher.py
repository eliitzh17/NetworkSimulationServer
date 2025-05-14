from app.rabbit_mq.rabbit_mq_client import RabbitMQClient
from app.models.simulation_models import LinkBusMessage
from typing import List
from app.rabbit_mq.publishers.base_publisher import BasePublisher
import os
class PostLinkRunPublisher(BasePublisher):
    def __init__(self, rabbit_mq_client: RabbitMQClient):
        super().__init__(rabbit_mq_client, 'post_run_publisher', os.getenv('POST_LINK_EXCHANGE'))

    def _serialize(self, obj):
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        return obj  # fallback for str, dict, etc.
    
    async def publish_post_links_execution_messages(self, simulation_id: str, is_failed: bool):
        message = [{"simulation_id": simulation_id, "is_failed": is_failed}]
        await self._publish_messages(message, os.getenv("POST_LINK_QUEUE"))

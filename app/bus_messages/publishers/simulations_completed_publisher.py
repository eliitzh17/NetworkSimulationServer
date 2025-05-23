from app.bus_messages.publishers.base_publisher import BasePublisher
from app.models.statuses_enums import EventType
import os

class SimulationsCompletedPublisher(BasePublisher):
    def __init__(self, db, rabbitmq_manager, exchange_name):
        super().__init__(rabbitmq_manager, 'simulations_completed_publisher', exchange_name, db)

    def _serialize(self, obj):
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        return obj  # fallback for str, dict, etc.
    
    # async def publish_post_links_execution_messages(self, simulation_id: str, is_failed: bool):
    #     message = [{"simulation_id": simulation_id, "is_failed": is_failed}]
    #     await self._publish_messages(message, os.getenv("SIMULATIONS_COMPLETED_QUEUE"))

    async def run_outbox_publisher(self):
        await super().run_outbox_publisher(EventType.SIMULATIONS_COMPLETED, os.getenv("SIMULATIONS_COMPLETED_QUEUE"))


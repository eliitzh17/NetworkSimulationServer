from app.models.statuses_enums import EventType
from pydantic import BaseModel, Field
from typing import List


class EventTypeToRoutingKey(BaseModel):
    event_type: EventType
    routing_key: str

class OutboxPublisher(BaseModel):
    event_type_to_routing_key: List[EventTypeToRoutingKey]
    max_parallel: int
    initial_delay: int
    max_retries: int
    retry_delay: int
    max_concurrent_publishes: int = 10
    batch_size: int = 100
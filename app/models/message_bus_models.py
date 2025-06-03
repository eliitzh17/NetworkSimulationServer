from app.models.statuses_enums import EventType
from pydantic import BaseModel, Field
from typing import List


class EventTypeToRoutingKey(BaseModel):
    event_type: EventType
    routing_key: str

class OutboxPublisher(BaseModel):
    max_parallel: int
    initial_delay: int
    max_retries: int
    retry_delay: int
    max_messages_to_publish: int
    batch_size_events_query: int
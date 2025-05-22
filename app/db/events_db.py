from app.utils.logger import LoggerManager
from app.core.exceptions import DatabaseError, ValidationError
from datetime import UTC
import os
from pymongo.errors import PyMongoError
from app.models.events_models import BaseEvent
from typing import List, Optional
from bson.objectid import ObjectId
from datetime import datetime

class EventsDB:
    """
    Repository for CRUD operations on Events documents in MongoDB.
    Adds meta fields: _id, created_at, updated_at.
    """
    db_logger = LoggerManager.get_logger('events_db')

    def __init__(self, db):
        self.collection = db[os.getenv("EVENTS_COLLECTION")]

    async def store_events(self, events: List[BaseEvent], session=None) -> str:
        try:
            docs = [event.model_dump(by_alias=True) for event in events]
            for event in docs:
                event["created_at"] = datetime.now(UTC)
                event["updated_at"] = datetime.now(UTC)
            result = await self.collection.insert_many(docs, session=session)
            self.db_logger.info(f"Created Events with ids {result.inserted_ids}")
            return str(result.inserted_ids)
        except PyMongoError as e:
            self.db_logger.error(f"Database error while creating Events: {str(e)}")
            raise DatabaseError(f"Failed to create Events: {str(e)}") from e
        except Exception as e:
            self.db_logger.error(f"Unexpected error while creating Events: {str(e)}")
            raise ValidationError(f"Invalid Events data: {str(e)}") from e
        
    async def get_events(self, event_id: str) -> Optional[BaseEvent]:
        try:
            doc = await self.collection.find_one({"_id": ObjectId(event_id)})
            if doc:
                return BaseEvent.model_validate(doc)
            self.db_logger.warning(f"Event with id {event_id} not found")
            return None
        except PyMongoError as e:
            self.db_logger.error(f"Database error while fetching Event {event_id}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve Event: {str(e)}") from e
        except Exception as e:
            self.db_logger.error(f"Unexpected error while fetching Event {event_id}: {str(e)}")
            raise ValidationError(f"Error processing Event data: {str(e)}") from e
        
    async def update_event(self, event_id: str, update_data: BaseEvent) -> bool:
        try:
            result = await self.collection.update_one(
                {"_id": ObjectId(event_id)},
                {"$set": update_data.model_dump()}
            )
            if result.modified_count > 0:
                self.db_logger.info(f"Updated Event with id {event_id}")
                return True
            self.db_logger.warning(f"No Event updated for id {event_id}")
            return False
        except PyMongoError as e:
            self.db_logger.error(f"Database error while updating Event {event_id}: {str(e)}")
            raise DatabaseError(f"Failed to update Event: {str(e)}") from e
        except Exception as e:
            self.db_logger.error(f"Unexpected error while updating Event {event_id}: {str(e)}")
            raise ValidationError(f"Error processing Event data: {str(e)}") from e
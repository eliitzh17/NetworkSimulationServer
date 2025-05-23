from app.utils.logger import LoggerManager
from app.business_logic.exceptions import DatabaseError, ValidationError
from datetime import UTC
import os
from pymongo.errors import PyMongoError
from app.models.events_models import BaseEvent
from typing import List, Optional, Type
from bson.objectid import ObjectId
from datetime import datetime
import pymongo
from pymongo import MongoClient

class EventsDB:
    """
    Repository for CRUD operations on Events documents in MongoDB.
    Adds meta fields: _id, created_at, updated_at.
    """

    def __init__(self, db):
        self.db = db
        self.collection = self.db[os.getenv("EVENTS_COLLECTION")]
        self.logger = LoggerManager.get_logger('events_db')

    async def store_events(self, events: List[BaseEvent], session=None) -> str:
        self.logger.info(f"store_events {len(events)} events")
        try:
            docs = [event.model_dump(by_alias=True) for event in events]
            for event in docs:
                event["created_at"] = datetime.now(UTC)
                event["updated_at"] = datetime.now(UTC)
            result = await self.collection.insert_many(docs, session=session)
            self.logger.info(f"Created Events with ids {result.inserted_ids}")
            return str(result.inserted_ids)
        except PyMongoError as e:
            self.logger.error(f"Database error while creating Events: {str(e)}")
            raise DatabaseError(f"Failed to create Events: {str(e)}") from e
        except Exception as e:
            self.logger.error(f"Unexpected error while creating Events: {str(e)}")
            raise ValidationError(f"Invalid Events data: {str(e)}") from e
        
    async def get_event(self, event_id: str) -> Optional[BaseEvent]:
        try:
            doc = await self.collection.find_one({"_id": event_id})
            if doc:
                return BaseEvent.model_validate(doc)
            self.logger.warning(f"Event with id {event_id} not found")
            return None
        except PyMongoError as e:
            self.logger.error(f"Database error while fetching Event {event_id}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve Event: {str(e)}") from e
        except Exception as e:
            self.logger.error(f"Unexpected error while fetching Event {event_id}: {str(e)}")
            raise ValidationError(f"Error processing Event data: {str(e)}") from e
        
    async def update_event(self, event_id: str, update_data: BaseEvent) -> bool:
        self.logger.info(f"update_event event_id: {event_id}")
        try:
            result = await self.collection.update_one(
                {"_id": event_id},
                {"$set": update_data.model_dump()}
            )
            if result.modified_count > 0:
                self.logger.info(f"Updated Event with id {event_id}")
                return True
            self.logger.warning(f"No Event updated for id {event_id}")
            return False
        except PyMongoError as e:
            self.logger.error(f"Database error while updating Event {event_id}: {str(e)}")
            raise DatabaseError(f"Failed to update Event: {str(e)}") from e
        except Exception as e:
            self.logger.error(f"Unexpected error while updating Event {event_id}: {str(e)}")
            raise ValidationError(f"Error processing Event data: {str(e)}") from e

    async def find_events_by_filter(self, filter: dict, limit: int = 10) -> list[dict]:
        """
        Find events matching a filter, limited by 'limit'.
        Returns a list of BaseEvent objects.
        """
        try:
            cursor = self.collection.find(filter).sort("created_at", pymongo.DESCENDING).limit(limit)
            docs = await cursor.to_list(length=limit)
            return docs
        except PyMongoError as e:
            self.logger.error(f"Database error while finding Events: {str(e)}")
            raise DatabaseError(f"Failed to find Events: {str(e)}") from e
        except Exception as e:
            self.logger.error(f"Unexpected error while finding Events: {str(e)}")
            raise ValidationError(f"Error processing Events data: {str(e)}") from e
        
    
    async def update_events_published(self, event_ids: list[str]) -> tuple[int, list[dict]]:
        """
        Set published=True for all events with IDs in event_ids.
        Returns a tuple: (number of updated documents, list of up-to-date documents).
        """
        self.logger.info(f"update_events_published event_ids: {event_ids}")
        try:
            # Convert string IDs to ObjectId if needed
            result = await self.collection.update_many(
                {"_id": {"$in": event_ids}},
                {"$set": {"published": True, "published_at": datetime.now(UTC), "updated_at": datetime.now(UTC)}}
            )
            self.logger.info(f"Marked {result.modified_count} events as published.")
            if result.modified_count > 0:
                # Fetch the up-to-date documents in a single query
                updated_docs = await self.collection.find({"_id": {"$in": event_ids}}).to_list(length=len(event_ids))
                return result.modified_count, updated_docs
            else:
                raise ValidationError(f"No events marked as published")
        except PyMongoError as e:
            self.logger.error(f"Database error while updating published Events: {str(e)}")
            raise DatabaseError(f"Failed to update published Events: {str(e)}") from e
        except Exception as e:
            self.logger.error(f"Unexpected error while updating published Events: {str(e)}")
            raise ValidationError(f"Error processing published Events: {str(e)}") from e

    async def update_events_handled(self, event_ids: list[str]) -> int:
        """
        Set is_handled=True for all events with IDs in event_ids.
        Returns the number of updated documents.
        """
        self.logger.info(f"Will mark {len(event_ids)} events as handled")
        try:
            filter_query = {"_id": {"$in": [id for id in event_ids]}}
            update_command = {"$set": {"is_handled": True, "updated_at": datetime.now(UTC)}}
            
            self.logger.debug(f"update_many filter: {filter_query}")
            self.logger.debug(f"update_many update: {update_command}")
            result = await self.collection.update_many(
                filter_query,
                update_command
            )
            if result.modified_count > 0:
                self.logger.info(f"Marked {result.modified_count} events as handled. ✅")
                return result.modified_count
            else:
                raise ValidationError(f"No events marked as handled")

        except PyMongoError as e:
            self.logger.error(f"Database error while updating handled Events: {str(e)}")
            raise DatabaseError(f"Failed to update handled Events: {str(e)}") from e
        except Exception as e:
            self.logger.error(f"Unexpected error while updating handled Events: {str(e)}")
            raise ValidationError(f"Error processing handled Events: {str(e)}") from e
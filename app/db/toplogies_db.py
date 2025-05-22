from app.models.pageination_models import CursorPaginationResponse, CursorPaginationRequest
from app.utils.logger import LoggerManager
from app.core.error_handlers import DatabaseError, ValidationError
from datetime import datetime, UTC
from bson.objectid import ObjectId
from app.models.topolgy_models import Topology
from typing import List, Optional
from pydantic import TypeAdapter
import os
from pymongo.errors import PyMongoError
from pymongo import UpdateOne
from pymongo.errors import BulkWriteError

class TopologiesDB:
    """
    Repository for CRUD operations on Topologies documents in MongoDB.
    Adds meta fields: _id, created_at, updated_at.
    """
    db_logger = LoggerManager.get_logger('topologies_db')

    def __init__(self, db):
        self.collection = db[os.getenv("TOPOLOGIES_COLLECTION")]

    async def store_topologies(self, topologies: List[Topology], session=None) -> List[Topology]:
        try:
            docs = []
            for topology in topologies:
                topology_dict = topology.model_dump(by_alias=True)
                topology_dict["created_at"] = datetime.now(UTC)
                topology_dict["updated_at"] = datetime.now(UTC)
                docs.append(topology_dict)
            result = await self.collection.insert_many(docs, session=session)
            self.db_logger.info(f"Created Topologies with ids {result.inserted_ids}")

            cursor = self.collection.find({"_id": {"$in": result.inserted_ids}}, session=session)
            docs = await cursor.to_list(length=len(result.inserted_ids))
            return [Topology.model_validate(doc) for doc in docs]   
        except PyMongoError as e:
            self.db_logger.error(f"Database error while creating Topologies: {str(e)}")
            raise DatabaseError(f"Failed to create Topologies: {str(e)}") from e
        except Exception as e:
            self.db_logger.error(f"Unexpected error while creating Topologies: {str(e)}")
            raise ValidationError(f"Failed to create Topologies: {str(e)}") from e

    async def get_topology(self, sim_id: str) -> Optional[Topology]:
        try:
            doc = await self.collection.find_one({"sim_id": sim_id})
            if doc:
                self.db_logger.info(f"Fetched Topology with id {sim_id}")
                return Topology.model_validate(doc)
            self.db_logger.warning(f"Topology with id {sim_id} not found")
            return None
        except PyMongoError as e:
            self.db_logger.error(f"Database error while fetching Topolgies {sim_id}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve Topolgies: {str(e)}") from e
        except Exception as e:
            self.db_logger.error(f"Unexpected error while fetching Topolgies {sim_id}: {str(e)}")
            raise ValidationError(f"Error processing Topolgies data: {str(e)}") from e

    async def update_many(self, updates: list[tuple[str, Topology]]) -> int:
        """
        Update multiple Topologies by their sim_id using MongoDB bulk_write.
        Args:
            updates: List of (sim_id, Topology) tuples to update.
        Returns:
            int: Number of successfully updated documents.
        """
        operations = []
        for sim_id, update_data in updates:
            update_dict = update_data.model_dump()
            update_dict["updated_at"] = datetime.now(UTC)
            operations.append(
                UpdateOne({"sim_id": sim_id}, {"$set": update_dict})
            )
        try:
            if operations:
                result = await self.collection.bulk_write(operations)
                self.db_logger.info(f"Bulk updated {result.modified_count} Topologies")
                return result.modified_count
            return 0
        except BulkWriteError as e:
            self.db_logger.error(f"Bulk write error: {str(e)}")
            raise DatabaseError(f"Bulk update failed: {str(e)}") from e
        except PyMongoError as e:
            self.db_logger.error(f"Database error during bulk update: {str(e)}")
            raise DatabaseError(f"Bulk update failed: {str(e)}") from e
        except Exception as e:
            self.db_logger.error(f"Unexpected error during bulk update: {str(e)}")
            raise ValidationError(f"Bulk update failed: {str(e)}") from e 

    async def list_all_cursor(self, cursor_pagination_request: CursorPaginationRequest) -> CursorPaginationResponse:
        try:
            query = {}
            if cursor_pagination_request.cursor:
                try:
                    query['_id'] = {'$gt': ObjectId(cursor_pagination_request.cursor)}
                except Exception:
                    raise ValidationError('Invalid cursor value')
            cursor = self.collection.find(query).sort('_id', 1).limit(cursor_pagination_request.page_size)
            docs = await cursor.to_list(length=cursor_pagination_request.page_size)
            total = await self.collection.count_documents({}) if cursor_pagination_request.with_total else None
            if docs:
                next_cursor = str(docs[-1]['_id']) if len(docs) == cursor_pagination_request.page_size else None
            else:
                next_cursor = None
            items = TypeAdapter(List[Topology]).validate_python(docs)
            return CursorPaginationResponse(
                items=items,
                next_cursor=next_cursor,
                page_size=cursor_pagination_request.page_size,
                total=total
            )
        except PyMongoError as e:
            self.db_logger.error(f"Database error while cursor-paginating Topolgiess: {str(e)}")
            raise DatabaseError(f"Failed to list Topolgiess: {str(e)}") from e
        except Exception as e:
            self.db_logger.error(f"Unexpected error while cursor-paginating Topolgiess: {str(e)}")
            raise ValidationError(f"Error processing Topolgies data: {str(e)}") from e
from app.utils.logger import LoggerManager
from app.core.exceptions import DatabaseError, ValidationError
from datetime import datetime, UTC
import os
from pymongo.errors import PyMongoError
from app.models.topolgy_simulation_models import TopologySimulation
from typing import List
from bson.objectid import ObjectId
from pymongo import UpdateOne
from pymongo.bulk import BulkWriteError
from app.models.pageination_models import CursorPaginationRequest, CursorPaginationResponse
from pydantic import TypeAdapter

class TopologiesSimulationsDB:
    """
    Repository for CRUD operations on TopologiesSimulation documents in MongoDB.
    Adds meta fields: _id, created_at, updated_at.
    """
    db_logger = LoggerManager.get_logger('topologies_simulation_db')

    def __init__(self, db):
        self.collection = db[os.getenv("TOPOLOGIES_SIMULATIONS_COLLECTION")]

    async def store_topologies_simulations(self, topologies_simulations: List[TopologySimulation], session=None) -> List[TopologySimulation]:
        """
        Create a new simulation metadata document in the database.
        
        Args:
            topologies_simulations: List of TopologySimulation objects to be stored
            session: MongoDB session for transaction support
        Returns:
            List of TopologySimulation objects
        """
        try:
            docs = [simulation.model_dump(by_alias=True) for simulation in topologies_simulations]
            for simulation in docs:
                simulation["created_at"] = datetime.now(UTC)
                simulation["updated_at"] = datetime.now(UTC)
            result = await self.collection.insert_many(docs, session=session)
            self.db_logger.info(f"Created simulation metadata with ids {result.inserted_ids}")
            cursor = self.collection.find({"_id": {"$in": result.inserted_ids}}, session=session)
            new_docs = await cursor.to_list(length=len(result.inserted_ids))
            return [TopologySimulation.model_validate(doc) for doc in new_docs]
        except PyMongoError as e:
            self.db_logger.error(f"Database error while creating simulation metadata: {str(e)}")
            raise DatabaseError(f"Failed to create simulation metadata: {str(e)}") from e
        except Exception as e:
            self.db_logger.error(f"Unexpected error while creating simulation metadata: {str(e)}")
            raise ValidationError(f"Invalid simulation metadata: {str(e)}") from e
        
    async def get_topology_simulation(self, simulation_id: str) -> TopologySimulation:
        """
        Retrieve a list of TopologySimulation objects from the database based on the simulation_id.

        Args:
            simulation_id: The unique ID of the simulation

        Returns:
            List of TopologySimulation objects

        Raises:
            DatabaseError: If a database operation fails
            ValidationError: If the data is invalid
        """
        try:
            simulation = await self.collection.find_one({"_id": ObjectId(simulation_id)})
            return TopologySimulation(**simulation)
        except PyMongoError as e:
            self.db_logger.error(f"Database error while fetching topologies simulations: {str(e)}")
            raise DatabaseError(f"Failed to fetch topologies simulations: {str(e)}") from e
        except Exception as e:
            self.db_logger.error(f"Unexpected error while fetching topologies simulations: {str(e)}")
            raise ValidationError(f"Invalid topologies simulations: {str(e)}") from e
        
    async def _cursor_paginate(self, query: dict, cursor_pagination_request: CursorPaginationRequest) -> CursorPaginationResponse:
        try:
            if cursor_pagination_request.cursor:
                try:
                    query['_id'] = {'$gt': ObjectId(cursor_pagination_request.cursor)}
                except Exception:
                    raise ValidationError('Invalid cursor value')
            cursor = self.collection.find(query).sort('_id', 1).limit(cursor_pagination_request.page_size)
            docs = await cursor.to_list(length=cursor_pagination_request.page_size)
            total = await self.collection.count_documents(query) if cursor_pagination_request.with_total else None
            if docs:
                next_cursor = str(docs[-1]['_id']) if len(docs) == cursor_pagination_request.page_size else None
            else:
                next_cursor = None
            items = TypeAdapter(List[TopologySimulation]).validate_python(docs)
            return CursorPaginationResponse(
                items=items,
                next_cursor=next_cursor,
                page_size=cursor_pagination_request.page_size,
                total=total
            )
        except PyMongoError as e:
            self.db_logger.error(f"Database error while cursor-paginating simulations: {str(e)}")
            raise DatabaseError(f"Failed to list simulations: {str(e)}") from e
        except Exception as e:
            self.db_logger.error(f"Unexpected error while cursor-paginating simulations: {str(e)}")
            raise ValidationError(f"Error processing simulation data: {str(e)}") from e

    async def list_all_simulations(self, cursor_pagination_request: CursorPaginationRequest) -> CursorPaginationResponse:
        return await self._cursor_paginate({}, cursor_pagination_request)

    async def get_topologies_simulations_by_topology_id(self, topology_id: str, cursor_pagination_request: CursorPaginationRequest) -> CursorPaginationResponse:
        return await self._cursor_paginate({"topology._id": topology_id}, cursor_pagination_request)

    async def update_simulations(self, updates: list[tuple[str, TopologySimulation]]) -> int:
        """
        Update multiple Topologies by their sim_id using MongoDB bulk_write.
        Args:
            updates: List of (sim_id, Topology) tuples to update.
        Returns:
            int: Number of successfully updated documents.
        """
        operations = []
        for simulation_id, update_data in updates:
            update_dict = update_data.model_dump(by_alias=True)
            update_dict["updated_at"] = datetime.now(UTC)
            operations.append(
                UpdateOne({"_id": ObjectId(simulation_id)}, {"$set": update_dict})
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
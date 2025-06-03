from app.utils.logger import LoggerManager
from app.business_logic.exceptions import DatabaseError, ValidationError
from datetime import datetime, UTC
import os
from pymongo.errors import PyMongoError
from app.models.topolgy_simulation_models import TopologySimulation
from typing import List, Optional
from bson.objectid import ObjectId
from pymongo import UpdateOne
from pymongo.bulk import BulkWriteError
from app.models.pageination_models import CursorPaginationRequest, CursorPaginationResponse
from pydantic import TypeAdapter
from app.models.statuses_enums import TopologyStatusEnum, LinkStatusEnum
from app.app_container import app_container
from pymongo.collection import Collection

class TopologiesSimulationsDB:
    """
    Repository for CRUD operations on TopologiesSimulation documents in MongoDB.
    Adds meta fields: _id, created_at, updated_at.
    """
    def __init__(self, db):
        self.config = app_container.config()
        self.db = db
        self.collection: Collection = db[self.config.TOPOLOGIES_SIMULATIONS_COLLECTION]
        self.logger = LoggerManager.get_logger('topologies_simulations_db')

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
            self.logger.info(f"Created simulation metadata with ids {result.inserted_ids}")
            cursor = self.collection.find({"_id": {"$in": result.inserted_ids}}, session=session)
            new_docs = await cursor.to_list(length=len(result.inserted_ids))
            return [TopologySimulation.model_validate(doc) for doc in new_docs]
        except PyMongoError as e:
            self.logger.error(f"Database error while creating simulation metadata: {str(e)}")
            raise DatabaseError(f"Failed to create simulation metadata: {str(e)}") from e
        except Exception as e:
            self.logger.error(f"Unexpected error while creating simulation metadata: {str(e)}")
            raise ValidationError(f"Invalid simulation metadata: {str(e)}") from e
        
    async def get_topology_simulation(self, simulation_id: str, session=None) -> TopologySimulation:
        """
        Retrieve a TopologySimulation object from the database based on the simulation_id.

        Args:
            simulation_id: The unique ID of the simulation
            session: MongoDB session for transaction support

        Returns:
            TopologySimulation object

        Raises:
            DatabaseError: If a database operation fails
            ValidationError: If the data is invalid
        """
        try:
            simulation = await self.collection.find_one({"_id": simulation_id}, session=session)
            if simulation is None:
                self.logger.error(f"Simulation {simulation_id} not found")
                return None
            return TypeAdapter(TopologySimulation).validate_python(simulation)
        except PyMongoError as e:
            self.logger.error(f"Database error while fetching topologies simulations: {str(e)}")
            raise DatabaseError(f"Failed to fetch topologies simulations: {str(e)}") from e
        except Exception as e:
            self.logger.error(f"Unexpected error while fetching topologies simulations: {str(e)}")
            raise ValidationError(f"Invalid topologies simulations: {str(e)}") from e
        
    async def _cursor_paginate(self, query: dict, cursor_pagination_request: CursorPaginationRequest, session=None) -> CursorPaginationResponse[TopologySimulation]:
        try:
            if cursor_pagination_request.cursor:
                try:
                    query['_id'] = {'$gt': cursor_pagination_request.cursor}
                except Exception:
                    raise ValidationError('Invalid cursor value')
            cursor = self.collection.find(query, session=session).sort('_id', 1).limit(cursor_pagination_request.page_size)
            docs = await cursor.to_list(length=cursor_pagination_request.page_size)
            total = await self.collection.count_documents(query, session=session) if cursor_pagination_request.with_total else None
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
            self.logger.error(f"Database error while cursor-paginating simulations: {str(e)}")
            raise DatabaseError(f"Failed to list simulations: {str(e)}") from e
        except Exception as e:
            self.logger.error(f"Unexpected error while cursor-paginating simulations: {str(e)}")
            raise ValidationError(f"Error processing simulation data: {str(e)}") from e

    async def list_all_simulations(self, cursor_pagination_request: CursorPaginationRequest, session=None) -> CursorPaginationResponse[TopologySimulation]:
        return await self._cursor_paginate({}, cursor_pagination_request, session=session)

    async def get_topologies_simulations_by_topology_id(self, topology_id: str, cursor_pagination_request: CursorPaginationRequest, session=None) -> CursorPaginationResponse[TopologySimulation]:
        return await self._cursor_paginate({"topology._id": topology_id}, cursor_pagination_request, session=session)

    async def update_simulation(self, simulation_id: str, update_data: TopologySimulation, ignore_row_version: bool = False, session=None) -> int:
        """
        Update a single TopologySimulation by its sim_id using optimistic concurrency control (row_version).
        Args:
            simulation_id: The ID of the simulation to update.
            update_data: The TopologySimulation object with updated data.
            row_version: The expected current row_version for concurrency control.
            session: MongoDB session for transaction support
        Returns:
            int: Number of successfully updated documents (1 if successful, 0 otherwise).
        Raises:
            ValidationError: If the row_version does not match (concurrent update detected).
        """
        update_dict = update_data.model_dump(by_alias=True)
        update_dict["updated_at"] = datetime.now(UTC)
        # Increment row_version for optimistic concurrency
        current_row_version = update_data.row_version
        update_dict["row_version"] = update_data.row_version + 1 if not ignore_row_version else None
        try:
            result = await self.collection.update_one(
                {"_id": simulation_id, "row_version": current_row_version if not ignore_row_version else None},
                {"$set": update_dict},
                session=session
            )
            if result.modified_count == 0:
                self.logger.error(f"Row version mismatch or simulation {simulation_id} not found for update.")
                raise ValidationError(f"Update failed: row_version mismatch or simulation not found.")
            self.logger.info(f"Updated simulation {simulation_id} with new row_version {update_data.row_version}")
            return result.modified_count
        except PyMongoError as e:
            self.logger.error(f"Database error during update: {str(e)}")
            raise DatabaseError(f"Update failed: {str(e)}") from e
        except Exception as e:
            self.logger.error(f"Unexpected error during update: {str(e)}")
            raise ValidationError(f"Update failed: {str(e)}") from e

    async def get_simulations_by_statuses(self, simulation_statuses: List[TopologyStatusEnum], link_statuses: List[LinkStatusEnum], cursor_pagination_request: CursorPaginationRequest, session=None) -> CursorPaginationResponse[TopologySimulation]:
        """
        Retrieve simulations filtered by their simulation status.

        Args:
            simulation_statuses: List of TopologyStatusEnum values to filter by
            link_statuses: List of LinkStatusEnum values to filter by
            cursor_pagination_request: Pagination request object
            session: MongoDB session for transaction support

        Returns:
            CursorPaginationResponse with filtered simulations
        """
        query = {
            "$and": [
                {"status": {"$in": simulation_statuses}},
                {"links_execution_state.processed_links.status": {"$in": link_statuses}}
            ]
        }   
        return await self._cursor_paginate(query, cursor_pagination_request, session=session)
    
    async def get_simulations_by_ids_and_status(self, simulation_ids: List[str], simulation_statuses: List[TopologyStatusEnum], limit: int = 100, session=None) -> List[TopologySimulation]:
        """
        Retrieve multiple TopologySimulation objects from the database based on their IDs and status.

        Args:
            simulation_ids: List of simulation IDs to retrieve
            simulation_statuses: List of TopologyStatusEnum values to filter by
            limit: Maximum number of simulations to return (default: 100)
            session: MongoDB session for transaction support

        Returns:
            List of TopologySimulation objects

        Raises:
            DatabaseError: If a database operation fails
            ValidationError: If the data is invalid
        """
        try:
            query = {
                "$and": [
                    {"_id": {"$in": simulation_ids}},
                    {"status": {"$in": simulation_statuses}}
                ]
            }
            cursor = self.collection.find(query, session=session).limit(limit)
            docs = await cursor.to_list(length=limit)
            if not docs:
                self.logger.warning(f"No simulations found for ids: {simulation_ids} and statuses: {simulation_statuses}")
                return []
            return TypeAdapter(List[TopologySimulation]).validate_python(docs)
        except PyMongoError as e:
            self.logger.error(f"Database error while fetching simulations by ids and status: {str(e)}")
            raise DatabaseError(f"Failed to fetch simulations: {str(e)}") from e
        except Exception as e:
            self.logger.error(f"Unexpected error while fetching simulations by ids and status: {str(e)}")
            raise ValidationError(f"Invalid simulation data: {str(e)}") from e
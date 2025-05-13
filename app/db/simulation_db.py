from typing import Optional, List
from datetime import datetime, UTC
from pydantic import TypeAdapter
from bson.errors import InvalidId
from pymongo.errors import PyMongoError
from app.models.simulation_models import Simulation
from app.utils.logger import LoggerManager
from app.core.exceptions import DatabaseError, ValidationError

class SimulationDB:
    """
    Repository for CRUD operations on Simulation documents in MongoDB.
    Adds meta fields: _id, created_at, updated_at.
    """
    db_logger = LoggerManager.get_logger('db')

    def __init__(self, db):
        self.collection = db["simulations"]

    async def store_simulation(self, simulation: Simulation) -> str:
        try:
            doc = simulation.model_dump(by_alias=True)
            doc["created_at"] = datetime.now(UTC)
            doc["updated_at"] = datetime.now(UTC)
            result = await self.collection.insert_one(doc)
            self.db_logger.info(f"Created simulation with id {result.inserted_id}")
            return str(result.inserted_id)
        except PyMongoError as e:
            self.db_logger.error(f"Database error while creating simulation: {str(e)}")
            raise DatabaseError(f"Failed to create simulation: {str(e)}") from e
        except Exception as e:
            self.db_logger.error(f"Unexpected error while creating simulation: {str(e)}")
            raise ValidationError(f"Invalid simulation data: {str(e)}") from e

    async def get_simulation(self, sim_id: str) -> Optional[Simulation]:
        try:
            doc = await self.collection.find_one({"sim_id": sim_id})
            if doc:
                self.db_logger.info(f"Fetched simulation with id {sim_id}")
                return Simulation.model_validate(doc)
            self.db_logger.warning(f"Simulation with id {sim_id} not found")
            return None
        except InvalidId as e:
            self.db_logger.error(f"Invalid simulation ID format: {sim_id}: {str(e)}")
            raise ValidationError(f"Invalid simulation ID format: {sim_id}") from e
        except PyMongoError as e:
            self.db_logger.error(f"Database error while fetching simulation {sim_id}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve simulation: {str(e)}") from e
        except Exception as e:
            self.db_logger.error(f"Unexpected error while fetching simulation {sim_id}: {str(e)}")
            raise ValidationError(f"Error processing simulation data: {str(e)}") from e

    async def update(self, sim_id: str, update_data: dict) -> bool:
        try:
            update_data["updated_at"] = datetime.now(UTC)
            result = await self.collection.update_one(
                {"sim_id": sim_id}, {"$set": update_data}
            )
            if result.modified_count > 0:
                self.db_logger.info(f"Updated simulation with id {sim_id}")
                return True
            self.db_logger.warning(f"No simulation updated for id {sim_id}")
            return False
        except InvalidId as e:
            self.db_logger.error(f"Invalid simulation ID format for update: {sim_id}: {str(e)}")
            raise ValidationError(f"Invalid simulation ID format: {sim_id}") from e
        except PyMongoError as e:
            self.db_logger.error(f"Database error while updating simulation {sim_id}: {str(e)}")
            raise DatabaseError(f"Failed to update simulation: {str(e)}") from e
        except Exception as e:
            self.db_logger.error(f"Unexpected error while updating simulation {sim_id}: {str(e)}")
            raise ValidationError(f"Invalid update data: {str(e)}") from e

    async def delete(self, sim_id: str) -> bool:
        try:
            result = await self.collection.delete_one({"sim_id": sim_id})
            if result.deleted_count > 0:
                self.db_logger.info(f"Deleted simulation with id {sim_id}")
                return True
            self.db_logger.warning(f"No simulation deleted for id {sim_id}")
            return False
        except InvalidId as e:
            self.db_logger.error(f"Invalid simulation ID format for deletion: {sim_id}: {str(e)}")
            raise ValidationError(f"Invalid simulation ID format: {sim_id}") from e
        except PyMongoError as e:
            self.db_logger.error(f"Database error while deleting simulation {sim_id}: {str(e)}")
            raise DatabaseError(f"Failed to delete simulation: {str(e)}") from e
        except Exception as e:
            self.db_logger.error(f"Unexpected error while deleting simulation {sim_id}: {str(e)}")
            raise DatabaseError(f"Error while attempting to delete simulation: {str(e)}") from e

    async def list_all(self) -> List[Simulation]:
        try:
            cursor = self.collection.find()
            docs = await cursor.to_list(length=1000)
            self.db_logger.info(f"Listed all simulations, count: {len(docs)}")
            return TypeAdapter(List[Simulation]).validate_python(docs)
        except PyMongoError as e:
            self.db_logger.error(f"Database error while listing simulations: {str(e)}")
            raise DatabaseError(f"Failed to list simulations: {str(e)}") from e
        except Exception as e:
            self.db_logger.error(f"Unexpected error while listing simulations: {str(e)}")
            raise ValidationError(f"Error processing simulation data: {str(e)}") from e 
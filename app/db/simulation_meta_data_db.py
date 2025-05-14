from typing import Optional, List
from datetime import datetime
from pydantic import TypeAdapter
from bson.errors import InvalidId
from pymongo.errors import PyMongoError
from app.models.simulation_models import SimulationMetaData
from app.utils.logger import LoggerManager
from app.core.exceptions import DatabaseError, ValidationError
from datetime import UTC
class SimulationMetaDataDB:
    """
    Repository for CRUD operations on SimulationMetaData documents in MongoDB.
    Adds meta fields: _id, created_at, updated_at.
    """
    db_logger = LoggerManager.get_logger('db')

    def __init__(self, db):
        self.collection = db["simulation_meta_data"]

    async def store_meta_data(self, meta_data: SimulationMetaData) -> str:
        """
        Create a new simulation metadata document in the database.
        
        Args:
            meta_data: SimulationMetaData object to be stored
            
        Returns:
            String representation of the MongoDB _id of the created document
            
        Raises:
            DatabaseError: If a database operation fails
            ValidationError: If the data is invalid
        """
        try:
            doc = meta_data.model_dump(by_alias=True)
            doc["created_at"] = datetime.now(UTC)
            doc["updated_at"] = datetime.now(UTC)
            result = await self.collection.insert_one(doc)
            self.db_logger.info(f"Created simulation metadata with id {result.inserted_id}")
            return str(result.inserted_id)
        except PyMongoError as e:
            self.db_logger.error(f"Database error while creating simulation metadata: {str(e)}")
            raise DatabaseError(f"Failed to create simulation metadata: {str(e)}") from e
        except Exception as e:
            self.db_logger.error(f"Unexpected error while creating simulation metadata: {str(e)}")
            raise ValidationError(f"Invalid simulation metadata: {str(e)}") from e

    async def get_by_id(self, id: str) -> Optional[SimulationMetaData]:
        """
        Retrieve simulation metadata by its unique ID.
        
        Args:
            id: The unique ID of the simulation metadata
            
        Returns:
            SimulationMetaData object or None if not found
            
        Raises:
            ValidationError: If the ID format is invalid
            DatabaseError: If a database operation fails
        """
        try:
            doc = await self.collection.find_one({"id": id})
            if doc:
                self.db_logger.info(f"Fetched simulation metadata with id {id}")
                return SimulationMetaData.model_validate(doc)
            self.db_logger.warning(f"Simulation metadata with id {id} not found")
            return None
        except InvalidId as e:
            self.db_logger.error(f"Invalid metadata ID format: {id}: {str(e)}")
            raise ValidationError(f"Invalid metadata ID format: {id}") from e
        except PyMongoError as e:
            self.db_logger.error(f"Database error while fetching metadata {id}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve simulation metadata: {str(e)}") from e
        except Exception as e:
            self.db_logger.error(f"Unexpected error while fetching metadata {id}: {str(e)}")
            raise ValidationError(f"Error processing metadata: {str(e)}") from e

    async def get_by_sim_id(self, sim_id: str) -> Optional[SimulationMetaData]:
        """
        Retrieve simulation metadata by simulation ID.
        
        Args:
            sim_id: The simulation ID associated with the metadata
            
        Returns:
            SimulationMetaData object or None if not found
            
        Raises:
            ValidationError: If the sim_id format is invalid
            DatabaseError: If a database operation fails
        """
        try:
            doc = await self.collection.find_one({"sim_id": sim_id})
            if doc:
                self.db_logger.info(f"Fetched simulation metadata for sim_id {sim_id}")
                return SimulationMetaData.model_validate(doc)
            self.db_logger.warning(f"Simulation metadata for sim_id {sim_id} not found")
            return None
        except PyMongoError as e:
            self.db_logger.error(f"Database error while fetching metadata for sim_id {sim_id}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve simulation metadata: {str(e)}") from e
        except Exception as e:
            self.db_logger.error(f"Unexpected error while fetching metadata for sim_id {sim_id}: {str(e)}")
            raise ValidationError(f"Error processing metadata: {str(e)}") from e

    async def update(self, id: str, update_data: SimulationMetaData) -> bool:
        """
        Update simulation metadata fields.
        
        Args:
            id: The unique ID of the simulation metadata to update
            update_data: Dictionary containing the fields to update
            
        Returns:
            True if the update was successful, False if no document was updated
            
        Raises:
            ValidationError: If the ID format is invalid
            DatabaseError: If a database operation fails
        """
        try:
            update_dict = update_data.model_dump()
            update_dict["updated_at"] = datetime.now(UTC)
            result = await self.collection.update_one(
                {"id": id}, {"$set": update_dict}
            )
            if result.modified_count > 0:
                self.db_logger.info(f"Updated simulation metadata with id {id}")
                return True
            self.db_logger.warning(f"No simulation metadata updated for id {id}")
            return False
        except InvalidId as e:
            self.db_logger.error(f"Invalid metadata ID format for update: {id}: {str(e)}")
            raise ValidationError(f"Invalid metadata ID format: {id}") from e
        except PyMongoError as e:
            self.db_logger.error(f"Database error while updating metadata {id}: {str(e)}")
            raise DatabaseError(f"Failed to update simulation metadata: {str(e)}") from e
        except Exception as e:
            self.db_logger.error(f"Unexpected error while updating metadata {id}: {str(e)}")
            raise ValidationError(f"Invalid update data: {str(e)}") from e

    async def delete(self, id: str) -> bool:
        """
        Delete simulation metadata by its ID.
        
        Args:
            id: The unique ID of the simulation metadata to delete
            
        Returns:
            True if deletion was successful, False if no document was deleted
            
        Raises:
            ValidationError: If the ID format is invalid
            DatabaseError: If a database operation fails
        """
        try:
            result = await self.collection.delete_one({"id": id})
            if result.deleted_count > 0:
                self.db_logger.info(f"Deleted simulation metadata with id {id}")
                return True
            self.db_logger.warning(f"No simulation metadata deleted for id {id}")
            return False
        except InvalidId as e:
            self.db_logger.error(f"Invalid metadata ID format for deletion: {id}: {str(e)}")
            raise ValidationError(f"Invalid metadata ID format: {id}") from e
        except PyMongoError as e:
            self.db_logger.error(f"Database error while deleting metadata {id}: {str(e)}")
            raise DatabaseError(f"Failed to delete simulation metadata: {str(e)}") from e
        except Exception as e:
            self.db_logger.error(f"Unexpected error while deleting metadata {id}: {str(e)}")
            raise DatabaseError(f"Error while attempting to delete metadata: {str(e)}") from e

    async def list_all(self) -> List[SimulationMetaData]:
        """
        List all simulation metadata documents.
        
        Returns:
            List of SimulationMetaData objects
            
        Raises:
            DatabaseError: If a database operation fails
            ValidationError: If there's an error processing the data
        """
        try:
            cursor = self.collection.find()
            docs = await cursor.to_list(length=1000)
            self.db_logger.info(f"Listed all simulation metadata, count: {len(docs)}")
            return TypeAdapter(List[SimulationMetaData]).validate_python(docs)
        except PyMongoError as e:
            self.db_logger.error(f"Database error while listing metadata: {str(e)}")
            raise DatabaseError(f"Failed to list simulation metadata: {str(e)}") from e
        except Exception as e:
            self.db_logger.error(f"Unexpected error while listing metadata: {str(e)}")
            raise ValidationError(f"Error processing metadata: {str(e)}") from e
    
    async def delete_by_sim_id(self, sim_id: str) -> bool:
        """
        Delete simulation metadata by simulation ID.
        
        Args:
            sim_id: The simulation ID associated with the metadata to delete
            
        Returns:
            True if deletion was successful, False if no document was deleted
            
        Raises:
            DatabaseError: If a database operation fails
        """
        try:
            result = await self.collection.delete_one({"sim_id": sim_id})
            if result.deleted_count > 0:
                self.db_logger.info(f"Deleted simulation metadata for sim_id {sim_id}")
                return True
            self.db_logger.warning(f"No simulation metadata deleted for sim_id {sim_id}")
            return False
        except PyMongoError as e:
            self.db_logger.error(f"Database error while deleting metadata for sim_id {sim_id}: {str(e)}")
            raise DatabaseError(f"Failed to delete simulation metadata: {str(e)}") from e
        except Exception as e:
            self.db_logger.error(f"Unexpected error while deleting metadata for sim_id {sim_id}: {str(e)}")
            raise DatabaseError(f"Error while attempting to delete metadata: {str(e)}") from e

from motor.motor_asyncio import AsyncIOMotorClient
from config import get_config
from app.core.exceptions import DatabaseError
from app.utils.logger import LoggerManager

COLLECTION_NAME = "simulations"

class MongoDBConnectionManager:
    """
    MongoDB connection manager for async operations using Motor.
    """
    db_logger = LoggerManager.get_logger('mongodb')
    
    def __init__(self):
        config = get_config()
        self.uri = config.MONGODB_URI
        self.db_name = config.MONGODB_DB
        self.client = None
        self.db = None

    async def connect(self):
        try:
            self.db_logger.info(f"Connecting to MongoDB at {self.uri}")
            self.client = AsyncIOMotorClient(self.uri)
            self.db = self.client[self.db_name]
            # Ping the database to verify connection
            await self.client.admin.command('ping')
            self.db_logger.info(f"Successfully connected to MongoDB database: {self.db_name} ✅")
        except Exception as e:
            self.db_logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise DatabaseError(f"Could not connect to MongoDB: {str(e)}") from e
        
    async def ensure_indexes(self):
        try:
            # Ensure unique index on sim_id for simulations collection
            await self.db["simulations"].create_index(
                [("sim_id", 1)], unique=True, name="sim_id_unique_idx"
            )
            self.db_logger.info("Ensured unique index on 'sim_id' for 'simulations' collection.")

            # Ensure unique index on id for simulation_meta_data collection
            await self.db["simulation_meta_data"].create_index(
                [("id", 1)], unique=True, name="meta_id_unique_idx"
            )
            self.db_logger.info("Ensured unique index on 'id' for 'simulation_meta_data' collection.")

            # Ensure unique index on sim_id for simulation_meta_data collection
            await self.db["simulation_meta_data"].create_index(
                [("sim_id", 1)], name="meta_sim_id_unique_idx"
            )
            self.db_logger.info("Ensured unique index on 'sim_id' for 'simulation_meta_data' collection.")
        except Exception as e:
            self.db_logger.error(f"Error ensuring indexes: {str(e)}")
            raise DatabaseError(f"Could not ensure indexes: {str(e)}") from e

    async def close(self):
        try:
            if self.client:
                self.client.close()
                self.db_logger.info("MongoDB connection closed")
        except Exception as e:
            self.db_logger.error(f"Error while closing MongoDB connection: {str(e)}")
            # No need to re-raise here as this is a cleanup operation

    async def is_connected(self):
        """
        Checks if the MongoDB client is connected by attempting a ping.
        Returns True if connected, False otherwise.
        """
        if self.client is None:
            return False
        try:
            await self.client.admin.command('ping')
            return True
        except Exception:
            return False
from motor.motor_asyncio import AsyncIOMotorClient
from app.business_logic.exceptions import DatabaseError
from app.utils.logger import LoggerManager
from app.config import AppConfig

COLLECTION_NAME = "simulations"

class MongoDBConnectionManager:
    """
    MongoDB connection manager for async operations using Motor.
    """
    db_logger = LoggerManager.get_logger('mongodb')
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.uri = self.config.MONGODB_URI
        self.db_name = self.config.MONGODB_DB
        self.client: AsyncIOMotorClient = None
        self.db: AsyncIOMotorClient = None

    async def connect(self):
        try:
            self.db_logger.info(f"Connecting to MongoDB at {self.uri}")
            self.client = AsyncIOMotorClient(
                self.uri,
                maxPoolSize=self.config.MONGODB_MAX_POOL_SIZE,
                minPoolSize=self.config.MONGODB_MIN_POOL_SIZE,
                maxIdleTimeMS=self.config.MONGODB_MAX_IDLE_TIME_MS,
                retryWrites=self.config.MONGODB_RETRY_WRITES,
                retryReads=self.config.MONGODB_RETRY_READS
            )
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
            await self.db["events"].create_index(
                [("_id", 1)], 
                name="event_id_unique_idx"
            )
            await self.db["events"].create_index(
                [("published", 1), ("created_at", 1)],
                name="events_published_created_idx"
            )
            self.db_logger.info("Ensured indexes for 'events' collection.")

            await self.db["topologies"].create_index(
                [("_id", 1)], name="topolgy_id_unique_idx"
            )
            self.db_logger.info("Ensured index on 'topolgy_id' for 'topologies' collection.")

            await self.db["topologies_simulations"].create_index(
                [("_id", 1)], name="topolgy_simulation_id_unique_idx"
            )
            await self.db["topologies_simulations"].create_index(
                [("status", 1), ("updated_at", 1)],
                name="simulations_status_updated_idx"
            )
            self.db_logger.info("Ensured indexes for 'topologies_simulations' collection.")

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
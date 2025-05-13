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

    async def close(self):
        try:
            if self.client:
                self.client.close()
                self.db_logger.info("MongoDB connection closed")
        except Exception as e:
            self.db_logger.error(f"Error while closing MongoDB connection: {str(e)}")
            # No need to re-raise here as this is a cleanup operation

    def get_collection(self, collection_name=COLLECTION_NAME):
        if not self.client or not self.db:
            self.db_logger.error("Attempted to get collection without an established connection")
            raise DatabaseError("MongoDB connection not established. Call connect() first.")
        return self.db[collection_name]
import os
from dataclasses import dataclass
from typing import Type
from dotenv import load_dotenv
from app.utils.logger import LoggerManager
from app.business_logic.exceptions import ConfigError

# Get logger for configuration
logger = LoggerManager.get_logger("config")

try:
    # Load environment variables from a .env file into the environment.
    load_dotenv()
    logger.info("Environment variables loaded from .env file")
except Exception as e:
    logger.warning(f"Failed to load .env file: {str(e)}")

@dataclass()
class AppConfig:
    # Required settings (no defaults)
    MONGODB_URI: str
    MONGODB_DB: str
    RABBITMQ_URL: str

    # Base settings (with defaults)
    PORT: int = 8000
    LOG_LEVEL: str = "info"

    # MongoDB settings (with defaults)
    TOPOLOGIES_COLLECTION: str = 'topologies'
    LINKS_COLLECTION: str = 'links'
    TOPOLOGIES_SIMULATIONS_COLLECTION: str = 'topologies_simulations'
    EVENTS_COLLECTION: str = 'events'
    
    # MongoDB Connection Pool settings
    MONGODB_MAX_POOL_SIZE: int = 100
    MONGODB_MIN_POOL_SIZE: int = 10
    MONGODB_MAX_IDLE_TIME_MS: int = 30000
    MONGODB_RETRY_WRITES: bool = True
    MONGODB_RETRY_READS: bool = True

    # AMQP settings
    # Exchange names
    SIMULATION_EXCHANGE: str = "simulation.exchange"
    LINKS_EXCHANGE: str = "links.exchange"

    # Queue names
    SIMULATION_QUEUE: str = "simulation.queue"
    RUN_LINKS_QUEUE: str = "links.run.queue"
    
    # Routing keys
    NEW_SIMULATIONS_QUEUE: str = "simulation.new.queue"
    SIMULATIONS_UPDATE_QUEUE: str = "simulation.update.queue"
    SIMULATIONS_PAUSED_QUEUE: str = "simulation.paused.queue"
    SIMULATIONS_RESUMED_QUEUE: str = "simulation.resume.queue"
    SIMULATIONS_STOPPED_QUEUE: str = "simulation.stop.queue"
    SIMULATIONS_COMPLETED_QUEUE: str = "simulation.completed.queue"
    SIMULATIONS_RESTARTED_QUEUE: str = "simulation.restarted.queue"

    # Suffixes
    RETRY_SUFFIX: str = ".retry"
    DLX_SUFFIX: str = ".dlx"

    # Consumers
    SIMULATIONS_CONSUMER_MAX_CONCURRENT_TASKS: int = 10
    LINKS_CONSUMER_MAX_CONCURRENT_TASKS: int = 100

    # Producers
    PAGE_SIZE: int = 200
    MAX_SIMULATIONS_IN_PARALLEL_PRODUCER: int = 10
    MAX_LINKS_IN_PARALLEL_PRODUCER: int = 100
    MAX_SIMULATIONS_IN_PARALLEL_COMPLETED_PRODUCER: int = 10

    # Consumers
    PREFETCH_COUNT: int = 100

    # Retry settings
    QUEUE_TTL: int = 600000
    DLX_TTL: int = 86400000
    INITIAL_DELAY: int = 2
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 5

    # Message timeout
    MESSAGE_TIMEOUT: int = 600

    # page query 
    PAGE_LIMIT = 1000


    def to_env(self):
        """
        Set all config variables as environment variables.
        """
        for field in self.__dataclass_fields__:
            value = getattr(self, field)
            if value is not None:
                os.environ[field] = str(value)
                
    def get(self, key: str) -> str:
        if not hasattr(self, key):
            raise ConfigError(f"Invalid key: {key}")
        return getattr(self, key)

class ProdConfig(AppConfig):
    pass

class DevConfig(AppConfig):
    pass 
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
    # This allows configuration via .env for local development and deployment.
    load_dotenv()
    logger.info("Environment variables loaded from .env file")
except Exception as e:
    logger.warning(f"Failed to load .env file: {str(e)}")

@dataclass(frozen=True)
class BaseConfig:
    MONGODB_URI: str
    MONGODB_DB: str
    RABBITMQ_URL: str
    RABBITMQ_MAX_RETRIES: int = 3
    RABBITMQ_INITIAL_RETRY_DELAY: int = 1
    RABBITMQ_RETRY_QUEUE_TTL: int = 5000
    RABBITMQ_RETRY_EXCHANGE_SUFFIX: str = "_dlx"
    RABBITMQ_RETRY_QUEUE_SUFFIX: str = "_retry"
    RABBITMQ_PREFETCH_COUNT: int = 5
    MAX_SIMULATIONS_IN_PARALLEL: int = 5
    INITIAL_DELAY: int = 1
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 10
    PORT: int = 8000
    LOG_LEVEL: str = "info"
    SIMULATION_EXCHANGE = "simulation_exchange"
    NEW_SIMULATIONS_QUEUE = "new_simulation_queue"
    SIMULATIONS_UPDATE_QUEUE = "simulation_update_queue"
    SIMULATIONS_PAUSED_QUEUE="paused_simulation_queue"
    SIMULATIONS_RESUMED_QUEUE="resume_simulation_queue"
    SIMULATIONS_STOPPED_QUEUE="stop_simulation_queue"
    SIMULATIONS_COMPLETED_QUEUE="completed_simulation_queue"

    LINKS_EXCHANGE = "links_exchange"
    RUN_LINKS_QUEUE = "run_links"

    #db's names
    TOPOLOGIES_COLLECTION='topolgies'
    LINKS_COLLECTION='links'
    TOPOLOGIES_SIMULATIONS_COLLECTION='topolgies_simulations'
    EVENTS_COLLECTION='events'

    @staticmethod
    def from_env(db_env_var_key: str) -> "BaseConfig":
        try:
            return BaseConfig(
                MONGODB_URI=os.environ["MONGODB_URI"],
                MONGODB_DB=os.environ[db_env_var_key],
                RABBITMQ_URL=os.environ["RABBITMQ_URL"],
                RABBITMQ_MAX_RETRIES=int(os.getenv("RABBITMQ_MAX_RETRIES", 3)),
                RABBITMQ_INITIAL_RETRY_DELAY=int(os.getenv("RABBITMQ_INITIAL_RETRY_DELAY", 1)),
                RABBITMQ_RETRY_QUEUE_TTL=int(os.getenv("RABBITMQ_RETRY_QUEUE_TTL", 5000)),
                RABBITMQ_PREFETCH_COUNT=int(os.getenv("RABBITMQ_PREFETCH_COUNT", 5)),
                MAX_SIMULATIONS_IN_PARALLEL=int(os.getenv("MAX_SIMULATIONS_IN_PARALLEL", 5)),
                INITIAL_DELAY=int(os.getenv("INITIAL_DELAY", 1)),
                MAX_RETRIES=int(os.getenv("MAX_RETRIES", 3)),
                RETRY_DELAY=int(os.getenv("RETRY_DELAY", 10)),
            )
        except KeyError as e:
            logger.error(f"Missing required environment variable: {e}")
            raise ConfigError(f"Missing required environment variable: {e}")

    def to_env(self):
        """
        Set all config variables as environment variables.
        """
        for field in self.__dataclass_fields__:
            value = getattr(self, field)
            if value is not None:
                os.environ[field] = str(value)

class ProdConfig(BaseConfig):
    @staticmethod
    def from_env() -> "ProdConfig":
        return ProdConfig(**BaseConfig.from_env("MONGODB_DB_PROD").__dict__)

class DevConfig(BaseConfig):
    @staticmethod
    def from_env() -> "DevConfig":
        return DevConfig(**BaseConfig.from_env("MONGODB_DB_DEV").__dict__)

def get_config() -> BaseConfig:
    env = os.getenv("ENV", "").lower()
    if env == "prod":
        config = ProdConfig.from_env()
    elif env == "dev":
        config = DevConfig.from_env()
    else:
        logger.error("ENV environment variable must be set to 'dev' or 'prod'.")
        raise ConfigError("ENV environment variable must be set to 'dev' or 'prod'.")
    config.to_env()
    return config 
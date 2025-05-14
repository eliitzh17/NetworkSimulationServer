import os
from dataclasses import dataclass
from typing import Type
from dotenv import load_dotenv
from app.utils.logger import LoggerManager
from app.core.exceptions import ConfigError

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
            )
        except KeyError as e:
            logger.error(f"Missing required environment variable: {e}")
            raise ConfigError(f"Missing required environment variable: {e}")

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
        return ProdConfig.from_env()
    elif env == "dev":
        return DevConfig.from_env()
    else:
        logger.error("ENV environment variable must be set to 'dev' or 'prod'.")
        raise ConfigError("ENV environment variable must be set to 'dev' or 'prod'.") 
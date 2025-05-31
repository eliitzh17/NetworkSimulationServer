import os
from app.config.base import AppConfig, ProdConfig, DevConfig
from app.utils.logger import LoggerManager
from app.business_logic.exceptions import ConfigError

logger = LoggerManager.get_logger("config")

def get_config() -> AppConfig:
    env = os.getenv("ENV", "").lower()
    
    # Get base config
    if env == "prod":
        config = ProdConfig(
            MONGODB_URI=os.environ["MONGODB_URI"],
            MONGODB_DB=os.environ["MONGODB_DB"],
            RABBITMQ_URL=os.environ["RABBITMQ_URL"]
        )
    elif env == "dev":
        config = DevConfig(
            MONGODB_URI=os.environ["MONGODB_URI"],
            MONGODB_DB=os.environ["MONGODB_DB"],
            RABBITMQ_URL=os.environ["RABBITMQ_URL"]
        )
    else:
        logger.error("ENV environment variable must be set to 'dev' or 'prod'.")
        raise ConfigError("ENV environment variable must be set to 'dev' or 'prod'.")
    
    config.to_env()
    return config

__all__ = ['get_config', 'AppConfig', 'ProdConfig', 'DevConfig'] 
import os
from dotenv import load_dotenv
from app.utils.logger import LoggerManager
from app.core.exceptions import ConfigError
from typing import Optional, Type

# Get logger for configuration
logger = LoggerManager.get_logger("config")

try:
    # Load environment variables from a .env file into the environment.
    # This allows configuration via .env for local development and deployment.
    load_dotenv()
    logger.info("Environment variables loaded from .env file")
except Exception as e:
    logger.warning(f"Failed to load .env file: {str(e)}")

class BaseConfig:
    MONGODB_URI: Optional[str] = None
    MONGODB_DB: Optional[str] = None
    RABBITMQ_URL: Optional[str] = None
    # Other truly common defaults or settings can go here

    @classmethod
    def _load_from_env(cls, db_env_var_key: str, config_name_log: str):
        mongodb_uri_val = os.getenv("MONGODB_URI")
        mongodb_db_val = os.getenv(db_env_var_key)
        rabbitmq_url_val = os.getenv("RABBITMQ_URL")
        
        if not mongodb_uri_val:
            msg = f"MONGODB_URI environment variable not set for {config_name_log}."
            logger.error(msg)
            raise ConfigError(msg)
        cls.MONGODB_URI = mongodb_uri_val

        if not mongodb_db_val:
            msg = f"{db_env_var_key} environment variable not set for {config_name_log}."
            logger.error(msg)
            raise ConfigError(msg)
        cls.MONGODB_DB = mongodb_db_val

        if not rabbitmq_url_val:
            msg = f"RABBITMQ_URL environment variable not set for {config_name_log}."
            logger.error(msg)
            raise ConfigError(msg)
        cls.RABBITMQ_URL = rabbitmq_url_val
        
        logger.info(f"Successfully loaded settings for {config_name_log} ✅")
        logger.info(f"  MONGODB_URI: {cls.MONGODB_URI}")
        logger.info(f"  MONGODB_DB: {cls.MONGODB_DB} (from env var '{db_env_var_key}')")

# Add environment-specific config classes
class ProdConfig(BaseConfig):
    pass

class DevConfig(BaseConfig):
    pass

_config_cache = {} # Cache for loaded configuration classes

def get_config() -> Type[BaseConfig]:
    env_value = os.getenv("ENV")
    if not env_value:
        logger.error("ENV environment variable not set.")
        raise ConfigError("ENV environment variable must be set to 'dev' or 'prod'.")

    env = env_value.lower()

    if env in _config_cache: # Return cached config if already loaded for this env
        return _config_cache[env]

    selected_config_class: Type[BaseConfig]
    db_key_for_env: str
    config_name_log: str

    if env == "prod":
        selected_config_class = ProdConfig
        db_key_for_env = "MONGODB_DB_PROD"
        config_name_log = "ProdConfig"
    elif env == "dev":
        selected_config_class = DevConfig
        db_key_for_env = "MONGODB_DB_DEV"
        config_name_log = "DevConfig"
    else:
        msg = f"Invalid value for ENV environment variable: '{env_value}'. Must be 'dev' or 'prod'."
        logger.error(msg)
        raise ConfigError(msg)

    try:
        # Load variables into the selected class itself
        selected_config_class._load_from_env(db_key_for_env, config_name_log)
        _config_cache[env] = selected_config_class # Cache the loaded class
        return selected_config_class
    except ConfigError: # Re-raise ConfigError to ensure it's not caught by the generic Exception
        raise 
    except Exception as e:
        # This catch is for unexpected errors during the _load_from_env call or other issues
        logger.critical(f"Critical error loading configuration for {config_name_log}: {str(e)}")
        raise ConfigError(f"Unexpected error during {config_name_log} setup: {str(e)}") from e 
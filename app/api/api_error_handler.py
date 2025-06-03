"""
API-specific error handling utilities.
Provides decorators and handlers for API endpoints.
"""
from functools import wraps
from fastapi import HTTPException
from app.utils.logger import LoggerManager
from app.business_logic.exceptions import (
    NetworkSimulationError,
    DatabaseError,
    ValidationError,
    SimulationError,
    ConfigError,
    ResourceError
)

logger = LoggerManager.get_logger('api_error_handler')

def handle_api_exceptions(func):
    """
    Decorator to handle exceptions in API endpoints.
    Provides consistent error handling and logging across all API endpoints.
    
    Usage:
        @handle_api_exceptions
        async def my_endpoint():
            ...
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except HTTPException as e:
            if e.status_code == 404:
                logger.info(f"Resource not found: {str(e)}")
            raise e
        except ValidationError as e:
            logger.warning(f"Validation error: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
        except DatabaseError as e:
            logger.error(f"Database error: {str(e)}")
            raise HTTPException(status_code=503, detail="Database service unavailable")
        except SimulationError as e:
            logger.error(f"Simulation error: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
        except ConfigError as e:
            logger.error(f"Configuration error: {str(e)}")
            raise HTTPException(status_code=500, detail="Configuration error")
        except ResourceError as e:
            logger.error(f"Resource error: {str(e)}")
            raise HTTPException(status_code=503, detail="Resource unavailable")
        except NetworkSimulationError as e:
            logger.error(f"Network simulation error: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
        except Exception as e:
            logger.critical(f"Unexpected error in {func.__name__}: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")
    return wrapper 
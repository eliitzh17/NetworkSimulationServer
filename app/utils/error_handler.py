"""
Error handling utilities for the application.
Provides helper functions for standardized error handling.
"""
import functools
import traceback
from app.utils.logger import LoggerManager
from app.core.exceptions import NetworkSimulationError

error_logger = LoggerManager.get_logger('error_handler')

def handle_exceptions(logger=None):
    """
    A decorator to handle exceptions in a standardized way.
    
    Args:
        logger: The logger to use. If None, uses the error_handler logger.
    
    Usage:
        @handle_exceptions(logger=some_logger)
        async def my_function():
            ...
    """
    if logger is None:
        logger = error_logger
        
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except NetworkSimulationError as e:
                # Log known application exceptions with their message
                logger.error(f"{e.__class__.__name__}: {str(e)}")
                raise e
            except Exception as e:
                # For unknown exceptions, log the full traceback
                logger.critical(
                    f"Unexpected error in {func.__name__}: {str(e)}\n"
                    f"Traceback: {traceback.format_exc()}"
                )
                raise NetworkSimulationError(f"Unexpected error: {str(e)}") from e
        return wrapper
    return decorator

def with_transaction(func):
    """
    A decorator to wrap database operations in a transaction.
    This ensures operations are atomic and can be rolled back on error.
    
    Usage:
        @with_transaction
        async def my_db_function(session, ...):
            ...
    """
    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        try:
            # Start transaction (if db supports it)
            async with await self.collection.database.client.start_session() as session:
                async with session.start_transaction():
                    # Call the original function with session
                    return await func(self, session, *args, **kwargs)
        except Exception as e:
            error_logger.error(f"Transaction failed in {func.__name__}: {str(e)}")
            raise e
    return wrapper 
"""
Application-level exception handlers.
These functions handle different types of exceptions that can occur in the application.
"""
from app.core.exceptions import (
    NetworkSimulationError,
    DatabaseError,
    SimulationError,
    ValidationError,
    ConfigError,
    ResourceError
)
from app.utils.logger import LoggerManager

error_logger = LoggerManager.get_logger('app_errors')

class ErrorHandlers:
    """
    A collection of static methods for handling different types of exceptions.
    """
    
    @staticmethod
    def handle_database_error(error: DatabaseError):
        """
        Handles database errors.
        Logs the error and potentially performs recovery operations.
        
        Args:
            error: The database error that occurred.
            
        Returns:
            dict: A standardized error response.
        """
        error_logger.error(f"Database error: {str(error)}")
        # Here you could add recovery logic, such as:
        # - Retry the operation
        # - Use a fallback database
        # - Return cached data
        return {
            "error": "database_error",
            "message": str(error),
            "status_code": 500,
            "retry": True
        }
    
    @staticmethod
    def handle_validation_error(error: ValidationError):
        """
        Handles validation errors.
        Logs the error and returns a standardized error response.
        
        Args:
            error: The validation error that occurred.
            
        Returns:
            dict: A standardized error response.
        """
        error_logger.warning(f"Validation error: {str(error)}")
        return {
            "error": "validation_error",
            "message": str(error),
            "status_code": 400,
            "retry": False
        }
    
    @staticmethod
    def handle_simulation_error(error: SimulationError):
        """
        Handles simulation-specific errors.
        Logs the error and potentially performs recovery operations.
        
        Args:
            error: The simulation error that occurred.
            
        Returns:
            dict: A standardized error response.
        """
        error_logger.error(f"Simulation error: {str(error)}")
        return {
            "error": "simulation_error",
            "message": str(error),
            "status_code": 500,
            "retry": True
        }
    
    @staticmethod
    def handle_config_error(error: ConfigError):
        """
        Handles configuration errors.
        Logs the error and potentially uses default configurations.
        
        Args:
            error: The configuration error that occurred.
            
        Returns:
            dict: A standardized error response.
        """
        error_logger.critical(f"Configuration error: {str(error)}")
        return {
            "error": "config_error",
            "message": str(error),
            "status_code": 500,
            "retry": False
        }
    
    @staticmethod
    def handle_resource_error(error: ResourceError):
        """
        Handles resource errors (e.g., memory, CPU).
        Logs the error and potentially frees up resources.
        
        Args:
            error: The resource error that occurred.
            
        Returns:
            dict: A standardized error response.
        """
        error_logger.error(f"Resource error: {str(error)}")
        return {
            "error": "resource_error",
            "message": str(error),
            "status_code": 503,
            "retry": True
        }
    
    @staticmethod
    def handle_generic_error(error: Exception):
        """
        Handles any other unexpected exceptions.
        Logs the error and returns a standardized error response.
        
        Args:
            error: The unexpected error that occurred.
            
        Returns:
            dict: A standardized error response.
        """
        error_logger.critical(f"Unexpected error: {str(error)}")
        return {
            "error": "internal_error",
            "message": "An unexpected error occurred. Please try again later.",
            "status_code": 500,
            "retry": False
        }
    
    @classmethod
    def get_error_handler(cls, error: Exception):
        """
        Gets the appropriate error handler for a given exception.
        
        Args:
            error: The exception to handle.
            
        Returns:
            function: The appropriate error handler function.
        """
        if isinstance(error, DatabaseError):
            return cls.handle_database_error
        elif isinstance(error, ValidationError):
            return cls.handle_validation_error
        elif isinstance(error, SimulationError):
            return cls.handle_simulation_error
        elif isinstance(error, ConfigError):
            return cls.handle_config_error
        elif isinstance(error, ResourceError):
            return cls.handle_resource_error
        else:
            return cls.handle_generic_error 
"""
Custom exception classes for the network simulation application.
Provides better error handling and more descriptive error messages.
"""

class NetworkSimulationError(Exception):
    """Base exception for all network simulation errors."""
    pass

class DatabaseError(NetworkSimulationError):
    """Exception raised for database connection and operation errors."""
    pass

class SimulationError(NetworkSimulationError):
    """Exception raised for errors during simulation execution."""
    pass

class ValidationError(NetworkSimulationError):
    """Exception raised for data validation errors."""
    pass

class ConfigError(NetworkSimulationError):
    """Exception raised for configuration errors."""
    pass

class ResourceError(NetworkSimulationError):
    """Exception raised for resource allocation or availability errors."""
    pass 
from abc import ABC, abstractmethod
from loguru import logger
from typing import Dict, Any
import threading

class AbstractLogger(ABC):
    """
    Abstract base class for loggers, enforcing best practices.
    """
    @abstractmethod
    def debug(self, message: str, **kwargs: Any) -> None:
        pass

    @abstractmethod
    def info(self, message: str, **kwargs: Any) -> None:
        pass

    @abstractmethod
    def warning(self, message: str, **kwargs: Any) -> None:
        pass

    @abstractmethod
    def error(self, message: str, **kwargs: Any) -> None:
        pass

    @abstractmethod
    def critical(self, message: str, **kwargs: Any) -> None:
        pass

class LoguruLogger(AbstractLogger):
    """
    Concrete logger implementation using Loguru.
    """
    def __init__(self, name: str = 'default'):
        self.name = name

    def debug(self, message: str, **kwargs: Any) -> None:
        logger.debug(f"[{self.name}] {message}", **kwargs)

    def info(self, message: str, **kwargs: Any) -> None:
        logger.info(f"[{self.name}] {message}", **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        logger.warning(f"[{self.name}] {message}", **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        logger.error(f"[{self.name}] {message}", **kwargs)

    def critical(self, message: str, **kwargs: Any) -> None:
        logger.critical(f"[{self.name}] {message}", **kwargs)

class LoggerManager:
    """
    Holds and manages logger instances.
    Thread-safe implementation.
    """
    _loggers: Dict[str, AbstractLogger] = {}
    _lock = threading.Lock()

    @classmethod
    def get_logger(cls, name: str = 'default') -> AbstractLogger:
        with cls._lock:
            if name not in cls._loggers:
                cls._loggers[name] = LoguruLogger(name)
            return cls._loggers[name]

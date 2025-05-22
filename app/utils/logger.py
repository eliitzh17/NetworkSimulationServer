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
    LEVELS = {
        'DEBUG': 10,
        'INFO': 20,
        'WARNING': 30,
        'ERROR': 40,
        'CRITICAL': 50
    }

    def __init__(self, name: str = 'default', level: str = 'INFO'):
        self.name = name
        self.level = level.upper()
        # Remove all handlers and add a new one with the specified level only once per process
        # (This is a simple approach; for more advanced use, consider handler management per logger)
        logger.remove()
        logger.add(lambda msg: print(msg, end=''), level=level)
        
    def set_level(self, level: str):
        self.level = level.upper()

    def _should_log(self, msg_level: str) -> bool:
        return self.LEVELS[msg_level] >= self.LEVELS[self.level]

    def debug(self, message: str, **kwargs: Any) -> None:
        if self._should_log('DEBUG'):
            logger.debug(f"[{self.name}] {message}", **kwargs)

    def info(self, message: str, **kwargs: Any) -> None:
        if self._should_log('INFO'):
            logger.info(f"[{self.name}] {message}", **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        if self._should_log('WARNING'):
            logger.warning(f"[{self.name}] {message}", **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        if self._should_log('ERROR'):
            logger.error(f"[{self.name}] {message}", **kwargs)

    def critical(self, message: str, **kwargs: Any) -> None:
        if self._should_log('CRITICAL'):
            logger.critical(f"[{self.name}] {message}", **kwargs)

class LoggerManager:
    """
    Holds and manages logger instances.
    Thread-safe implementation.
    """
    _loggers: Dict[str, AbstractLogger] = {}
    _lock = threading.Lock()

    @classmethod
    def get_logger(cls, name: str = 'default', level: str = 'DEBUG') -> AbstractLogger:
        with cls._lock:
            if name not in cls._loggers:
                cls._loggers[name] = LoguruLogger(name, level)
            return cls._loggers[name]

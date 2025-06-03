import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional, List, Set
from app.utils.logger import LoggerManager
from app.messageBroker.rabbit_mq_manager import RabbitMQManager

@dataclass
class QueueMetrics:
    """Data class to store queue metrics."""
    message_count: int = 0
    consumer_count: int = 0
    last_updated: float = 0

class BackpressureManager:
    """
    Manages backpressure for RabbitMQ publishers by monitoring queue sizes and consumer counts.
    Implements a dynamic delay mechanism based on queue load and consumer availability.
    """
    def __init__(
        self,
        rabbitmq_manager: RabbitMQManager,
        high_load_threshold: int = 500,
        medium_load_threshold: int = 250,
        base_delay: float = 2.0,
        max_delay: float = 30.0,
        metrics_cache_ttl: float = 5.0,
        consumer_queue_name: str = None
    ):
        """
        Initialize the backpressure manager.
        
        Args:
            rabbitmq_manager: The RabbitMQ manager instance
            logger: Logger instance for logging
            high_load_threshold: Number of messages that triggers maximum delay
            medium_load_threshold: Number of messages that triggers medium delay
            base_delay: Minimum delay in seconds
            max_delay: Maximum delay in seconds
            metrics_cache_ttl: Time-to-live for cached metrics in seconds
        """
        self.rabbitmq_manager = rabbitmq_manager
        self.logger = LoggerManager.get_logger(self.__class__.__name__)
        self.consumer_queue_name = consumer_queue_name
        self.queue_metrics: Dict[str, QueueMetrics] = {}
        self._metrics_lock = asyncio.Lock()
        
        # Configuration
        self.HIGH_LOAD_THRESHOLD = high_load_threshold
        self.MEDIUM_LOAD_THRESHOLD = medium_load_threshold
        self.BASE_DELAY = base_delay
        self.MAX_DELAY = max_delay
        self.METRICS_CACHE_TTL = metrics_cache_ttl
        
        # Statistics
        self.total_delays = 0
        self.total_delay_time = 0.0
        self.last_backpressure_time: Optional[datetime] = None

    async def _get_queue_metrics(self, queue_name: str) -> Optional[QueueMetrics]:
        """
        Get queue metrics with caching to prevent too frequent RabbitMQ calls.
        
        Args:
            queue_name: Name of the queue to get metrics for
            
        Returns:
            QueueMetrics object if successful, None if failed
        """
        async with self._metrics_lock:
            current_time = asyncio.get_event_loop().time()
            metrics = self.queue_metrics.get(queue_name)
            
            if metrics and (current_time - metrics.last_updated) < self.METRICS_CACHE_TTL:
                return metrics
                
            try:
                # Get queue and its metrics
                queue = await self.rabbitmq_manager.channel.declare_queue(
                    queue_name,
                    passive=True  # Only check if queue exists, don't try to create/modify it
                )
                
                # Get queue details using declare
                queue_info = await queue.declare()
                
                metrics = QueueMetrics()
                metrics.message_count = queue_info.message_count
                metrics.consumer_count = queue_info.consumer_count
                metrics.last_updated = current_time
                
                self.queue_metrics[queue_name] = metrics
                return metrics
            except Exception as e:
                self.logger.error(f"Error getting queue metrics for {queue_name}: {e}")
                return None

    async def calculate_delay(self, queue_name: str) -> float:
        """
        Calculate appropriate delay based on queue metrics.
        
        Args:
            queue_name: Name of the queue to monitor
            
        Returns:
            Calculated delay in seconds
        """
            
        max_queue_size = 0
        total_consumers = 0
        
        metrics = await self._get_queue_metrics(queue_name)
            
        if metrics:
            max_queue_size = max(max_queue_size, metrics.message_count)
            total_consumers += metrics.consumer_count
        
        if total_consumers == 0:
            self.logger.warning("No active consumers detected, applying maximum delay")
            return self.MAX_DELAY
            
        # Calculate messages per consumer
        messages_per_consumer = max_queue_size / total_consumers if total_consumers > 0 else float('inf')
        
        # Calculate delay based on queue size and consumer load
        if max_queue_size > self.HIGH_LOAD_THRESHOLD:
            delay = self.MAX_DELAY
        elif max_queue_size > self.MEDIUM_LOAD_THRESHOLD:
            # Linear scaling between MEDIUM_LOAD_THRESHOLD and HIGH_LOAD_THRESHOLD
            ratio = (max_queue_size - self.MEDIUM_LOAD_THRESHOLD) / (self.HIGH_LOAD_THRESHOLD - self.MEDIUM_LOAD_THRESHOLD)
            delay = self.BASE_DELAY + (self.MAX_DELAY - self.BASE_DELAY) * ratio
        else:
            delay = self.BASE_DELAY
            
        # Adjust delay based on messages per consumer
        if messages_per_consumer > 100:  # If each consumer has more than 100 messages
            delay = max(delay, self.MAX_DELAY * 0.5)
            
        return min(delay, self.MAX_DELAY)

    async def apply_backpressure(self) -> None:
        """
        Apply backpressure by calculating and waiting for the appropriate delay.
        
        Args:
            queue_name: Name of the queue to monitor for backpressure
        """
        delay = await self.calculate_delay(self.consumer_queue_name)
        
        if delay > self.BASE_DELAY:
            self.logger.info(f"Applying backpressure delay: {delay:.1f}s")
            self.total_delays += 1
            self.total_delay_time += delay
            self.last_backpressure_time = datetime.utcnow()
            
        await asyncio.sleep(delay)

    def get_statistics(self) -> Dict:
        """
        Get backpressure statistics.
        
        Returns:
            Dictionary containing backpressure statistics
        """
        return {
            "total_delays": self.total_delays,
            "total_delay_time": self.total_delay_time,
            "average_delay": self.total_delay_time / self.total_delays if self.total_delays > 0 else 0,
            "last_backpressure_time": self.last_backpressure_time.isoformat() if self.last_backpressure_time else None
        } 
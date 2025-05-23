from datetime import datetime
from typing import Dict, List
import aio_pika
from app.utils.logger import LoggerManager

class MessageBusMonitor:
    def __init__(self, rabbitmq_client, queues: Dict[str, aio_pika.Queue]):
        self.rabbitmq_client = rabbitmq_client
        self.queues = queues
        self.logger = LoggerManager.get_logger("message_bus_monitor")
        self.metrics = {
            "processed_messages": 0,
            "failed_messages": 0,
            "retried_messages": 0,
            "dlq_messages": 0,
            "processing_times": []
        }

    async def get_queue_metrics(self) -> Dict[str, Dict]:
        """Get metrics for all queues"""
        metrics = {}
        for name, queue in self.queues.items():
            queue_info = await queue.declare(passive=True)
            metrics[name] = {
                "message_count": queue_info.message_count,
                "consumer_count": queue_info.consumer_count,
                "last_updated": datetime.utcnow().isoformat()
            }
        return metrics

    async def get_processing_metrics(self) -> Dict:
        """Get message processing metrics"""
        return {
            "total_processed": self.metrics["processed_messages"],
            "total_failed": self.metrics["failed_messages"],
            "total_retried": self.metrics["retried_messages"],
            "total_dlq": self.metrics["dlq_messages"],
            "average_processing_time": sum(self.metrics["processing_times"]) / len(self.metrics["processing_times"]) if self.metrics["processing_times"] else 0
        }

    def record_message_processed(self, processing_time: float):
        """Record a successfully processed message"""
        self.metrics["processed_messages"] += 1
        self.metrics["processing_times"].append(processing_time)

    def record_message_failed(self):
        """Record a failed message"""
        self.metrics["failed_messages"] += 1

    def record_message_retried(self):
        """Record a retried message"""
        self.metrics["retried_messages"] += 1

    def record_message_dlq(self):
        """Record a message moved to DLQ"""
        self.metrics["dlq_messages"] += 1

    async def check_health(self) -> Dict[str, bool]:
        """Check the health of the message bus system"""
        try:
            connection = await self.rabbitmq_client.get_connection()
            channel = await connection.channel()
            
            health = {
                "connection": connection.is_closed is False,
                "channel": channel.is_closed is False,
                "queues": {}
            }

            for name, queue in self.queues.items():
                try:
                    await queue.declare(passive=True)
                    health["queues"][name] = True
                except Exception as e:
                    self.logger.error(f"Queue {name} health check failed: {e}")
                    health["queues"][name] = False

            return health
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {
                "connection": False,
                "channel": False,
                "queues": {name: False for name in self.queues.keys()}
            } 
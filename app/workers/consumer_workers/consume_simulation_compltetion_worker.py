import os
import asyncio
from aio_pika import ExchangeType
from app.bus_messages.rabbit_mq_client import RabbitMQClient
from app.bus_messages.rabbit_mq_manager import RabbitMQManager
from app.bus_messages.consumers.simulation_completed_consumer import SimulationCompletedConsumer
from app.utils.logger import LoggerManager
from app.app_container import app_container
from app.monitoring.message_bus_monitor import MessageBusMonitor

def main():
    asyncio.run(setup_and_run())

async def monitor_queues(monitor: MessageBusMonitor, logger):
    while True:
        try:
            queue_metrics = await monitor.get_queue_metrics()
            processing_metrics = await monitor.get_processing_metrics()
            health = await monitor.check_health()
            logger.info(f"Queue Metrics: {queue_metrics}")
            logger.info(f"Processing Metrics: {processing_metrics}")
            logger.info(f"Health Status: {health}")
            if queue_metrics.get("dlq", {}).get("message_count", 0) > 0:
                logger.warning(f"Messages in DLQ: {queue_metrics['dlq']['message_count']}")
            if not health["connection"] or not health["channel"]:
                logger.error("Message bus health check failed")
            await asyncio.sleep(60)
        except Exception as e:
            logger.error(f"Monitoring error: {e}")
            await asyncio.sleep(60)

async def setup_and_run():
    logger = LoggerManager.get_logger("simulation_completed_consumer")
    mongo_manager = app_container.mongo_manager()
    await mongo_manager.connect()
    db = mongo_manager.db

    rabbitmq_client = RabbitMQClient(os.getenv("RABBITMQ_URL"))
    exchange_configs = [
        {"name": os.getenv("SIMULATIONS_COMPLETED_EXCHANGE"), "type": ExchangeType.DIRECT, "durable": True},
    ]
    rabbitmq_manager = RabbitMQManager(rabbitmq_client, exchange_configs)
    await rabbitmq_manager.setup_exchanges()

    main_queue, retry_queue, dead_letter_queue = await rabbitmq_manager.setup_queue_with_retry(
        queue_name=os.getenv("SIMULATIONS_COMPLETED_QUEUE"),
        exchange_name=os.getenv("SIMULATIONS_COMPLETED_EXCHANGE")
    )

    queues = {
        "main": main_queue,
        "retry": retry_queue,
        "dlq": dead_letter_queue
    }
    monitor = MessageBusMonitor(rabbitmq_client, queues)

    consumer = SimulationCompletedConsumer(
        db, main_queue, logger,
        retry_queue=retry_queue,
        dead_letter_queue=dead_letter_queue,
        monitor=monitor
    )
    # Start monitoring in the background
    asyncio.create_task(monitor_queues(monitor, logger))
    await consumer.start_consuming()
    await asyncio.Future()  # Keep the worker alive

if __name__ == "__main__":
    main() 
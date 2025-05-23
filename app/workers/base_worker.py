import asyncio
from app.utils.logger import LoggerManager
from app.app_container import app_container
from app.bus_messages.publishers.base_publisher import BasePublisher
async def run_consumer_worker(consumer_class, logger_name, consumer_args=None):
    """
    Worker runner for consumers.
    :param consumer_class: The class to instantiate (e.g., SimulationConsumer, LinksConsumer)
    :param logger_name: Logger name for this worker
    :param consumer_args: Dict of extra args for the consumer constructor (besides db, logger).
    """
    logger = LoggerManager.get_logger(logger_name)
    logger.info(f"Starting {logger_name} consumer worker")

    mongo_manager = app_container.mongo_manager()
    try:
        await mongo_manager.connect()
        db = mongo_manager.db
        consumer_args = consumer_args or {}
        consumer = consumer_class(db, **consumer_args)
        await consumer.run_consumer()
        await asyncio.Future()  # Keeps the worker alive
    except Exception as e:
        logger.error(f"[!] Exception in {logger_name} consumer worker: {e}", exc_info=True)
        raise
    finally:
        logger.info(f"Closing {logger_name} consumer worker")
        await mongo_manager.close()


async def run_outbox_publisher_worker(publisher_class: BasePublisher, logger_name: str, publisher_args=None):
    """
    Worker runner for outbox publishers.
    :param publisher_class: The class to instantiate (e.g., Publisher)
    :param logger_name: Logger name for this worker
    :param publisher_args: Dict of extra args for the publisher constructor (besides db, logger).
    """
    logger = LoggerManager.get_logger(logger_name)
    logger.info(f"Starting {logger_name} outbox publisher worker")

    try:
        publisher_args = publisher_args or {}
        publisher = publisher_class(**publisher_args)
        await publisher.run_outbox_publisher()
        await asyncio.Future()  # Keeps the worker alive
    except Exception as e:
        logger.error(f"[!] Exception in {logger_name} outbox publisher worker: {e}", exc_info=True)
        raise e
    finally:
        logger.info(f"Closing {logger_name} outbox publisher worker")

# Deprecated: use run_consumer_worker or run_outbox_publisher_worker instead
# async def run_worker(consumer_class, logger_name, consumer_args=None):
#     ...

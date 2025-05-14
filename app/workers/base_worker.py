import asyncio
from app.utils.logger import LoggerManager
from app import container

async def run_worker(consumer_class, logger_name, consumer_args=None):
    """
    Generic worker runner for consumers.
    :param consumer_class: The consumer class to instantiate (e.g., SimulationConsumer, LinksConsumer)
    :param logger_name: Logger name for this worker
    :param consumer_args: Dict of extra args for the consumer constructor (besides db, rabbit_mq_client, logger)
    """
    config = container.config()
    logger = LoggerManager.get_logger(logger_name)
    logger.info(f"Starting {logger_name} worker")
    mongo_manager = container.mongo_manager()
    connection = None
    try:
        await mongo_manager.connect()
        db = mongo_manager.db
        rabbit_mq_client = container.rabbitmq_client()
        consumer_args = consumer_args or {}
        consumer = consumer_class(db, rabbit_mq_client, logger, **consumer_args)
        connection = await consumer.start()
        await asyncio.Future()  # Keep running
    except Exception as e:
        logger.error(f"[!] Exception in {logger_name} worker: {e}", exc_info=True)
        raise
    finally:
        logger.info(f"Closing {logger_name} worker")
        if connection:
            await connection.close()
        await mongo_manager.close()
    

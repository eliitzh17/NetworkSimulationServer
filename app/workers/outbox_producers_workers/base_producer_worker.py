import asyncio
from app.utils.logger import BasicLogger
from app.messageBroker.producers.base_producer import BaseProducer
from app.messageBroker.rabbit_mq_manager import RabbitMQManager
from app.app_container import app_container
from app.utils.logger import LoggerManager

class BaseProducerWorker:
    def __init__(self, db, rabbitmq_manager: RabbitMQManager):
        self.config = app_container.config()
        self.db = db
        self.rabbitmq_manager = rabbitmq_manager
        self.logger = LoggerManager.get_logger(self.__class__.__name__)

async def run_outbox_producer_worker(logger: BasicLogger, producer_class: BaseProducer, producer_args=None):
    """
    Worker runner for outbox producers.
    :param logger: The logger to use for the worker
    :param producer_class: The class to instantiate (e.g., SimulationsProducer)
    :param producer_args: Dict of extra args for the producer constructor (besides db, logger).
    """
    logger.info(f"Starting outbox producer worker")

    try:
        producer_args = producer_args or {}
        producer = producer_class(**producer_args)
        await producer.run_outbox_producer()
        await asyncio.Future()  # Keeps the worker alive
    except Exception as e:
        logger.error(f"[!] Exception in outbox producer worker: {e}", exc_info=True)
        raise e
    finally:
        logger.info(f"Closing outbox producer worker")

# Deprecated: use run_consumer_worker or run_outbox_publisher_worker instead
# async def run_worker(consumer_class, logger_name, consumer_args=None):
#     ...

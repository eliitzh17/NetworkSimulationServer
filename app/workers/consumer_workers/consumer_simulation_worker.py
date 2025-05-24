from app.workers.consumer_workers.base_consumer_worker import BaseConsumerWorker
from app.bus_messages.consumers.simulations_consumer import SimulationConsumer
from aio_pika import ExchangeType
import os

class SimulationConsumerWorker(BaseConsumerWorker):
    LOGGER_NAME = "simulation_consumer"
    EXCHANGE_ENV = "SIMULATION_EXCHANGE"
    EXCHANGE_TYPE = ExchangeType.DIRECT
    QUEUE_ENV = "NEW_SIMULATIONS_QUEUE"
    CONSUMER_CLASS = SimulationConsumer
    USE_CONFIG_FOR_RABBITMQ_URL = True
    USE_CONFIG_FOR_EXCHANGE = False
    USE_CONFIG_FOR_QUEUE = False

if __name__ == "__main__":
    SimulationConsumerWorker.main() 
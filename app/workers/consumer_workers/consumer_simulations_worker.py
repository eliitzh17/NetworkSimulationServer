import asyncio
from aio_pika import ExchangeType
from app.workers.consumer_workers.base_consumer_worker import BaseConsumerWorker
from app.messageBroker.consumers.simulations_consumer import SimulationConsumer


class SimulationConsumerWorker(BaseConsumerWorker):
    def __init__(self):
        super().__init__(
            logger="simulation_consumer",
            exchange_key_name="SIMULATION_EXCHANGE",
            exchange_type=ExchangeType.TOPIC,
            queue_key_name="SIMULATION_QUEUE",
            routing_key_pattern="simulation.*",
            consumer_class=SimulationConsumer
        )
        
if __name__ == "__main__":
    asyncio.run(SimulationConsumerWorker.main()) 
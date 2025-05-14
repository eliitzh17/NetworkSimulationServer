from app.rabbit_mq.consumers.simulations_consumer import SimulationConsumer
from app.workers.base_worker import run_worker
import os
import asyncio

if __name__ == "__main__":
    asyncio.run(run_worker(
        consumer_class=SimulationConsumer,
        logger_name="handle_simulation_worker"
    )) 
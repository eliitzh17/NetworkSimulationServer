from app.rabbit_mq.rabbit_mq_client import RabbitMQClient
from aio_pika import Message, ExchangeType
import json
import aio_pika
from app.utils.logger import LoggerManager
from app.models.simulation_models import Simulation
from typing import List
import asyncio
import os

class SimulationsPublisher:
    def __init__(self, rabbit_mq_client: RabbitMQClient):
        self.rabbit_mq_client = rabbit_mq_client
        self.logger = LoggerManager.get_logger('simulation_publisher')

    async def publish_simulations_messages(self, simulation_body: List[Simulation]):
        try:    
            self.logger.info(f"Publishing simulations messages: {simulation_body}")
            connection = await self.rabbit_mq_client.get_connection()
            async with connection:
                channel = await connection.channel()
                exchange = await channel.declare_exchange(
                    os.getenv("SIMULATION_EXCHANGE"), ExchangeType.FANOUT, durable=True
                )
                tasks = []
                for simulation in simulation_body:
                    message = Message(
                        body=json.dumps(simulation.model_dump()).encode(),
                        content_type="application/json",
                        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                    )
                    tasks.append(exchange.publish(message, routing_key=""))
                    await asyncio.gather(*tasks)
                    self.logger.info(f"Published {len(simulation_body)} simulations messages ✅")
        except Exception as e:
            self.logger.error(f"Error publishing simulations messages: {e}")
            raise e
        
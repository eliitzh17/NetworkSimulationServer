from app.rabbit_mq.rabbit_mq_client import RabbitMQClient
from aio_pika import Message, ExchangeType
import json
import aio_pika
import os
from app.models.simulation_models import LinkBusMessage
from typing import List
import asyncio
from app.utils.logger import LoggerManager
from aiormq.exceptions import ChannelInvalidStateError
import traceback

class LinksPublisher:
    def __init__(self, rabbit_mq_client: RabbitMQClient):
        self.rabbit_mq_client = rabbit_mq_client
        self.logger = LoggerManager.get_logger('links_publisher')
        
    async def publish_links_messages(self, links_body: List[LinkBusMessage]):
        max_retries = 3
        delay = 2  # seconds
        for attempt in range(max_retries):
            try:
                self.logger.info(f"Publishing links messages: {links_body}")
                connection = await self.rabbit_mq_client.get_connection()
                async with connection:
                    channel = await connection.channel()
                    exchange = await channel.declare_exchange(
                        os.getenv("LINKS_EXCHANGE"), ExchangeType.FANOUT, durable=True
                    )
                    tasks = []
                    for link in links_body:
                        message = Message(
                            body=json.dumps(link.model_dump()).encode(),
                            content_type="application/json",
                            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                        )
                        tasks.append(exchange.publish(message, routing_key=""))
                    await asyncio.gather(*tasks)
                    self.logger.info(f"Published {len(links_body)} links messages ✅")
                break  # Success, exit retry loop
            except ChannelInvalidStateError as e:
                self.logger.error(f"{self.__class__.__name__}[!] ChannelInvalidStateError on attempt {attempt+1}: {e}\n{traceback.format_exc()}")
                if attempt < max_retries - 1:
                    await self.rabbit_mq_client.reconnect()
                    await asyncio.sleep(delay)
                    continue
                else:
                    raise
            except Exception as e:
                self.logger.error(f"{self.__class__.__name__}[!] Error publishing links messages: {e}\n{traceback.format_exc()}")
                raise e

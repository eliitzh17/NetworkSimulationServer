import asyncio
import json
import os
import traceback
from abc import ABC, abstractmethod
from aio_pika import Message, ExchangeType
from aiormq.exceptions import ChannelInvalidStateError
from app.utils.logger import LoggerManager
from config import get_config

class BasePublisher(ABC):
    def __init__(self, rabbit_mq_client, logger_name: str, exchange_env: str):
        self.rabbit_mq_client = rabbit_mq_client
        self.logger = LoggerManager.get_logger(logger_name)
        self.exchange_env = exchange_env
        config = get_config()
        self.max_retries = getattr(config, 'RABBITMQ_MAX_RETRIES', 3)
        self.initial_delay = getattr(config, 'RABBITMQ_INITIAL_RETRY_DELAY', 1)

    @abstractmethod
    def _serialize(self, obj):
        pass
    
    async def _get_exchange(self, channel):
        return await channel.declare_exchange(
            self.exchange_env, ExchangeType.FANOUT, durable=True
        )

    def _create_message(self, item):
        return Message(
            body=json.dumps(self._serialize(item)).encode(),
            content_type="application/json",
            delivery_mode=2,  # PERSISTENT
        )

    #TODO: publish batch
    #TODO: understand rabbitmq batch limitation
    async def _publish_batch(self, exchange, items, routing_key):
        if not isinstance(items, (list, tuple)):
            raise TypeError(f"items must be a list or tuple, got {type(items).__name__}")
        if len(items) == 0:
            return
        tasks = [exchange.publish(self._create_message(item), routing_key=routing_key) for item in items]
        await asyncio.gather(*tasks)

    async def _publish_messages(self, body_list, routing_key=""):
        for attempt in range(self.max_retries):
            try:
                self.logger.info(f"Publishing messages: {body_list}")
                connection = await self.rabbit_mq_client.get_connection()
                #this connection will be disposed once block of code is finished
                channel = await connection.channel()
                exchange = await self._get_exchange(channel)
                await self._publish_batch(exchange, body_list, routing_key)
                self.logger.info(f"Published {len(body_list)} messages ✅")
                break
            except ChannelInvalidStateError as e:
                self.logger.error(f"{self.__class__.__name__}[!] ChannelInvalidStateError on attempt {attempt+1}: {e}\n{traceback.format_exc()}")
                if attempt < self.max_retries - 1:
                    await self.rabbit_mq_client.reconnect()
                    await asyncio.sleep(self.initial_delay * (2 ** attempt))
                    continue
                else:
                    raise
            except Exception as e:
                self.logger.error(f"{self.__class__.__name__}[!] Error publishing messages: {e}\n{traceback.format_exc()}")
                raise e 
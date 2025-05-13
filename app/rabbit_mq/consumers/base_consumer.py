import aio_pika
import json
from aio_pika import ExchangeType
from app.rabbit_mq.rabbit_mq_client import RabbitMQClient
from aiormq.exceptions import ChannelInvalidStateError
import traceback
import asyncio

class BaseConsumer:
    def __init__(self, db, rabbit_mq_client : RabbitMQClient, logger, exchange_name, queue_name, exchange_type=ExchangeType.FANOUT):
        self.db = db
        self.rabbit_mq_client = rabbit_mq_client
        self.logger = logger
        self.exchange_name = exchange_name
        self.queue_name = queue_name
        self.exchange_type = exchange_type
        self.channel = None
        self.exchange = None
        self.connection = None

    async def declare_exchange(self):
        if self.exchange is None:
            self.logger.info(f"Declaring exchange {self.exchange_name}")
            self.exchange = await self.channel.declare_exchange(
                self.exchange_name, self.exchange_type, durable=True
            )
        return self.exchange

    async def declare_queue(self):
        self.logger.info(f"Declaring queue {self.queue_name}")
        return await self.channel.declare_queue(
            self.queue_name, durable=True
        )

    async def start(self):
        self.logger.info(f"Connecting to RabbitMQ for {self.__class__.__name__}")
        self.connection = await self.rabbit_mq_client.get_connection()
        self.channel = await self.rabbit_mq_client.get_channel()
        await self.declare_exchange()
        queue = await self.declare_queue()
        await queue.bind(self.exchange)
        await queue.consume(self.on_message)
        self.logger.info(f" [*] Waiting for messages on {self.queue_name}. To exit press CTRL+C")
        return self.connection  # Keep connection open

    async def verify_connection(self):
        if self.connection.is_closed:
            self.logger.info(f" [*] Connection closed for {self.__class__.__name__}")
            await self.start()
            self.logger.info(f" [*] Connection reconnected for {self.__class__.__name__}")
        return self.connection

    async def on_message(self, message: aio_pika.IncomingMessage):
        self.logger.info(f" [*] Received new message for {self.__class__.__name__}")
        try:
            await self.verify_connection()
            async with message.process():
                data = json.loads(message.body.decode())
                await self.process_message(data)
        except ChannelInvalidStateError as e:
            self.logger.error(f"{self.__class__.__name__}[!] ChannelInvalidStateError: {e}\n{traceback.format_exc()}")
            await self.rabbit_mq_client.reconnect()
        except Exception as e:
            self.logger.error(f"{self.__class__.__name__} Error processing message: {e}\n{traceback.format_exc()}")
            raise e

    async def process_message(self, data):
        raise NotImplementedError("Subclasses must implement process_message()") 
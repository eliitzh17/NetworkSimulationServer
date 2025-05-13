import aio_pika
import json
from aio_pika import ExchangeType
from app.rabbit_mq.rabbit_mq_client import RabbitMQClient
from aiormq.exceptions import ChannelInvalidStateError
import traceback
import asyncio
from config import get_config

class BaseConsumer:
    def __init__(self, db, rabbit_mq_client: RabbitMQClient, logger, exchange_name, queue_name, exchange_type=ExchangeType.FANOUT):
        self.db = db
        self.rabbit_mq_client = rabbit_mq_client
        self.logger = logger
        self.exchange_name = exchange_name
        self.queue_name = queue_name
        self.exchange_type = exchange_type
        self.channel = None
        self.exchange = None
        self.connection = None
        self._load_config()

    def _load_config(self):
        config = get_config()
        self.max_retries = config.RABBITMQ_MAX_RETRIES
        self.retry_delay = config.RABBITMQ_INITIAL_RETRY_DELAY
        self.retry_queue_ttl = config.RABBITMQ_RETRY_QUEUE_TTL
        self.retry_exchange_suffix = config.RABBITMQ_RETRY_EXCHANGE_SUFFIX
        self.retry_queue_suffix = config.RABBITMQ_RETRY_QUEUE_SUFFIX

    async def declare_exchange(self):
        if self.exchange is None:
            self.logger.info(f"Declaring exchange {self.exchange_name}")
            self.exchange = await self.channel.declare_exchange(
                self.exchange_name, self.exchange_type, durable=True
            )
        return self.exchange

    async def declare_queue(self):
        self.logger.info(f"Declaring queue {self.queue_name}")
        dlx_name = f"{self.queue_name}{self.retry_exchange_suffix}"
        retry_queue_name = f"{self.queue_name}{self.retry_queue_suffix}"
        dlx = await self._declare_dlx(dlx_name)
        retry_queue = await self._declare_retry_queue(retry_queue_name, dlx)
        await retry_queue.bind(dlx, routing_key=self.queue_name)
        return await self._declare_main_queue(dlx_name)

    async def _declare_dlx(self, dlx_name):
        return await self.channel.declare_exchange(
            dlx_name,
            ExchangeType.DIRECT,
            durable=True
        )

    async def _declare_retry_queue(self, retry_queue_name, dlx):
        return await self.channel.declare_queue(
            retry_queue_name,
            durable=True,
            arguments={
                'x-dead-letter-exchange': self.exchange_name,
                'x-dead-letter-routing-key': self.queue_name,
                'x-message-ttl': self.retry_queue_ttl
            }
        )

    async def _declare_main_queue(self, dlx_name):
        return await self.channel.declare_queue(
            self.queue_name,
            durable=True,
            arguments={
                'x-dead-letter-exchange': dlx_name,
                'x-dead-letter-routing-key': self.queue_name
            }
        )

    async def start(self):
        self.logger.info(f"Connecting to RabbitMQ for {self.__class__.__name__}")
        await self._setup_connection_and_channel()
        await self.declare_exchange()
        queue = await self.declare_queue()
        await queue.bind(self.exchange)
        await queue.consume(self.on_message)
        self.logger.info(f" [*] Waiting for messages on {self.queue_name}. To exit press CTRL+C")
        return self.connection

    async def _setup_connection_and_channel(self):
        self.connection = await self.rabbit_mq_client.get_connection()
        self.channel = await self.rabbit_mq_client.get_channel()

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
                data = self._parse_message_body(message)
                retry_count = self._get_retry_count(message)
                if self._exceeded_max_retries(retry_count):
                    self.logger.error(f"Message exceeded maximum retry attempts ({self.max_retries})")
                    return
                try:
                    await self.process_message(data)
                except Exception as e:
                    await self._handle_processing_error(e, message, retry_count)
        except ChannelInvalidStateError as e:
            self.logger.error(f"{self.__class__.__name__}[!] ChannelInvalidStateError: {e}\n{traceback.format_exc()}")
            await self.rabbit_mq_client.reconnect()
        except Exception as e:
            self.logger.error(f"{self.__class__.__name__} Error processing message: {e}\n{traceback.format_exc()}")
            raise e

    def _parse_message_body(self, message):
        return json.loads(message.body.decode())

    def _get_retry_count(self, message):
        return message.headers.get('x-retry-count', 0) if message.headers else 0

    def _exceeded_max_retries(self, retry_count):
        return retry_count >= self.max_retries

    async def _handle_processing_error(self, error, message, retry_count):
        self.logger.error(f"Error processing message: {error}")
        delay = self.retry_delay * (2 ** retry_count)
        self.logger.info(f"Retrying in {delay} seconds (attempt {retry_count + 1}/{self.max_retries})")
        await asyncio.sleep(delay)
        headers = dict(message.headers) if message.headers else {}
        headers['x-retry-count'] = retry_count + 1
        await self.channel.default_exchange.publish(
            aio_pika.Message(
                body=message.body,
                headers=headers,
                delivery_mode=message.delivery_mode,
                content_type=message.content_type,
            ),
            routing_key=f"{self.queue_name}{self.retry_queue_suffix}"
        )

    async def process_message(self, data):
        raise NotImplementedError("Subclasses must implement process_message()") 
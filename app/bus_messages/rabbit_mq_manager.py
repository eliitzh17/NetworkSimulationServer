import asyncio
from aio_pika import ExchangeType, Queue, Exchange
from app.utils.logger import LoggerManager
from app.bus_messages.rabbit_mq_client import RabbitMQClient
from typing import List, Optional, Tuple
from config import get_config
import os

class RabbitMQManager:
    def __init__(self, rabbit_mq_client: RabbitMQClient, exchange_configs: List[dict]):
        """
        exchange_configs: List of dicts, each with keys: name, type (ExchangeType), durable (bool)
        """
        self.rabbit_mq_client = rabbit_mq_client
        self.exchange_configs = exchange_configs
        self.exchanges = {}
        self.channel = None
        self.logger = LoggerManager.get_logger('rabbit_mq_manager')
        self.config = self._load_config()

    def _load_config(self):
        config = get_config()
        self.max_retries = config.RABBITMQ_MAX_RETRIES
        self.retry_delay = config.RABBITMQ_INITIAL_RETRY_DELAY
        self.retry_queue_ttl = config.RABBITMQ_RETRY_QUEUE_TTL
        self.prefetch_count = config.RABBITMQ_PREFETCH_COUNT
        self.retry_exchange_suffix = config.RABBITMQ_RETRY_EXCHANGE_SUFFIX
        self.retry_queue_suffix = config.RABBITMQ_RETRY_QUEUE_SUFFIX

    async def setup_exchanges(self):
        self.logger.info("Setting up RabbitMQManager: connecting and declaring exchanges...")
        connection = await self.rabbit_mq_client.get_connection()
        self.channel = await connection.channel()
        self.logger.info(f"New Channel created, will use prefetch count: {self.prefetch_count}")
        await self.channel.set_qos(prefetch_count=self.prefetch_count)
        for cfg in self.exchange_configs:
            name = cfg['name']
            ex_type = cfg.get('type', ExchangeType.DIRECT)
            durable = cfg.get('durable', True)
            self.logger.info(f"Declaring exchange {name} (type={ex_type}, durable={durable})")
            exchange = await self.channel.declare_exchange(name, ex_type, durable=durable)
            self.exchanges[name] = exchange
        self.logger.info("All exchanges declared and cached.")

    def get_exchange(self, name) -> Optional[Exchange]:
        return self.exchanges.get(name)

    def get_channel(self):
        return self.channel

    async def _declare_dlx_exchange(self, exchange_name: str):
        self.logger.debug(f"Declaring DLX exchange {exchange_name}{self.retry_exchange_suffix}")
        dlx_exchange_name = f"{exchange_name}{self.retry_exchange_suffix}"
        dlx_exchange = await self.channel.declare_exchange(
            dlx_exchange_name,
            ExchangeType.DIRECT,
            durable=True
        )
        return dlx_exchange, dlx_exchange_name

    async def _declare_dead_letter_queue(self, queue_name: str, dlx_exchange):
        self.logger.debug(f"Declaring dead letter queue {queue_name}.dlq")
        dead_letter_queue_name = f"{queue_name}.dlq"
        dead_letter_queue = await self.channel.declare_queue(
            dead_letter_queue_name,
            durable=True
        )
        await dead_letter_queue.bind(dlx_exchange, routing_key=queue_name)
        return dead_letter_queue, dead_letter_queue_name

    async def _declare_retry_queue(self, queue_name: str, exchange_name: str, dlx_exchange, dead_letter_queue_name: str):
        self.logger.debug(f"Declaring retry queue {queue_name}{self.retry_queue_suffix}")
        retry_queue_name = f"{queue_name}{self.retry_queue_suffix}"
        retry_queue = await self.channel.declare_queue(
            retry_queue_name,
            durable=True,
            arguments={
                'x-dead-letter-exchange': exchange_name,
                'x-message-ttl': self.retry_queue_ttl,
                'x-dead-letter-routing-key': dead_letter_queue_name
            }
        )
        await retry_queue.bind(dlx_exchange, routing_key=queue_name)
        return retry_queue, retry_queue_name

    async def _declare_main_queue(self, queue_name: str, exchange_name: str, dlx_exchange_name: str, dead_letter_queue_name: str):
        self.logger.debug(f"Declaring main queue {queue_name}")
        main_queue = await self.channel.declare_queue(
            queue_name,
            durable=True,
            arguments={
                'x-dead-letter-exchange': dlx_exchange_name,
                'x-dead-letter-routing-key': dead_letter_queue_name  # Route to DLQ
            }
        )
        await main_queue.bind(exchange_name, routing_key=queue_name)
        return main_queue

    async def setup_queue_with_retry(
        self,
        queue_name: str,
        exchange_name: str,
        channel=None
    ) -> Tuple[Queue, Queue, Queue]:
        """
        Setup a queue with retry and DLX configuration.
        Returns (main_queue, retry_queue, dead_letter_queue)
        """
        channel = channel or self.channel
        if not channel:
            raise RuntimeError("RabbitMQManager not set up. Call setup() first.")
        exchange = self.get_exchange(exchange_name)
        if not exchange:
            raise ValueError(f"Exchange {exchange_name} not found")
        
        # Step 1: Setup DLX exchange
        dlx_exchange_name = f"{exchange_name}{self.retry_exchange_suffix}"
        dlx_exchange = await channel.declare_exchange(
            dlx_exchange_name,
            ExchangeType.DIRECT,
            durable=True
        )
        # Step 2: Setup dead letter queue
        dead_letter_queue_name = f"{queue_name}.dlq"
        dead_letter_queue = await channel.declare_queue(
            dead_letter_queue_name,
            durable=True
        )
        await dead_letter_queue.bind(dlx_exchange, routing_key=queue_name)
        # Step 3: Setup retry queue
        retry_queue_name = f"{queue_name}{self.retry_queue_suffix}"
        retry_queue = await channel.declare_queue(
            retry_queue_name,
            durable=True,
            arguments={
                'x-dead-letter-exchange': exchange_name,
                'x-message-ttl': self.retry_queue_ttl,
                'x-dead-letter-routing-key': dead_letter_queue_name
            }
        )
        await retry_queue.bind(dlx_exchange, routing_key=queue_name)
        # Step 4: Setup main queue with DLX
        main_queue = await channel.declare_queue(
            queue_name,
            durable=True,
            arguments={
                'x-dead-letter-exchange': dlx_exchange_name,
                'x-dead-letter-routing-key': dead_letter_queue_name  # Route to DLQ
            }
        )
        await main_queue.bind(exchange_name, routing_key=queue_name)
        return main_queue, retry_queue, dead_letter_queue

    async def create_consumer_channel(self):
        """Create a new channel for a consumer, with prefetch_count set."""
        connection = await self.rabbit_mq_client.get_connection()
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=self.prefetch_count)
        return channel 
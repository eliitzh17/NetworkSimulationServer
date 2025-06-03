from aio_pika import ExchangeType, Queue, Exchange, Channel
from app.utils.logger import LoggerManager
from app.messageBroker.rabbit_mq_client import RabbitMQClient
from aiormq.exceptions import ChannelPreconditionFailed, ChannelInvalidStateError, AMQPChannelError
from app.app_container import app_container
import asyncio
from typing import Optional

class RabbitMQManager:
    def __init__(self, rabbit_mq_client: RabbitMQClient):
        self.config = app_container.config()
        self.rabbit_mq_client = rabbit_mq_client
        self.exchanges = {}
        self.channel: Optional[Channel] = None
        self.logger = LoggerManager.get_logger('rabbit_mq_manager')

    async def create_consumer_channel(self):
        """Create a new channel for a consumer, with prefetch_count set."""
        connection = await self.rabbit_mq_client.get_connection()
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=self.config.PREFETCH_COUNT)
        return channel

    async def _safe_declare_queue(self, channel: Channel, queue_name: str, durable: bool, arguments: dict, max_retries: int = 3 ) -> Optional[Queue]:
        for attempt in range(max_retries):
            try:
                channel = await self._ensure_channel()
                return await channel.declare_queue(queue_name, durable=durable, arguments=arguments)
            except ChannelPreconditionFailed as e:
                self.logger.warning(f"Queue {queue_name} exists with different arguments. Attempting to delete and recreate... Error: {type(e).__name__}: {str(e)}")
                try:
                    channel = await self._ensure_channel()
                    # Check for existing bindings before deletion
                    try:
                        bindings = await channel.queue_bindings(queue_name)
                        if bindings:
                            self.logger.warning(f"Queue {queue_name} has {len(bindings)} bindings that will be removed")
                    except Exception as binding_error:
                        self.logger.warning(f"Could not check bindings for queue {queue_name}: {type(binding_error).__name__}: {str(binding_error)}")
                    
                    await channel.queue_delete(queue_name)
                    return await channel.declare_queue(queue_name, durable=durable, arguments=arguments)
                except Exception as e:
                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 2
                        self.logger.warning(f"Attempt {attempt + 1} failed for queue {queue_name}. Retrying in {wait_time} seconds... Error: {type(e).__name__}: {str(e)}")
                        await asyncio.sleep(wait_time)
                        continue
                    self.logger.error(f"Failed to recreate queue {queue_name} after {max_retries} attempts: {type(e).__name__}: {str(e)}")
                    raise
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2
                    self.logger.warning(f"Attempt {attempt + 1} failed for queue {queue_name}. Retrying in {wait_time} seconds... Error: {type(e).__name__}: {str(e)}")
                    await asyncio.sleep(wait_time)
                    continue
                self.logger.error(f"Failed to declare queue {queue_name} after {max_retries} attempts: {type(e).__name__}: {str(e)}")
                raise

    async def _ensure_channel(self) ->Channel:
        """Ensure channel is open and valid, recreate if necessary"""
        if self.channel is None or self.channel.is_closed:
            connection = await self.rabbit_mq_client.get_connection()
            self.channel = await connection.channel()
            await self.channel.set_qos(prefetch_count=self.config.PREFETCH_COUNT)
        return self.channel

    async def _safe_declare_exchange(self, exchange_name: str, ex_type: ExchangeType, durable: bool, max_retries: int = 3) -> Exchange:
        for attempt in range(max_retries):
            try:
                channel = await self._ensure_channel()
                return await channel.declare_exchange(exchange_name, ex_type, durable=durable)
            except (ChannelPreconditionFailed, AMQPChannelError) as e:
                self.logger.warning(f"Exchange {exchange_name} exists with different arguments or channel error. Attempting to delete and recreate... Error: {type(e).__name__}: {str(e)}")
                try:
                    channel = await self._ensure_channel()
                    # Check for existing bindings before deletion
                    try:
                        bindings = await channel.exchange_bindings(exchange_name)
                        if bindings:
                            self.logger.warning(f"Exchange {exchange_name} has {len(bindings)} bindings that will be removed")
                    except Exception as binding_error:
                        self.logger.warning(f"Could not check bindings for exchange {exchange_name}: {type(binding_error).__name__}: {str(binding_error)}")
                    
                    await channel.exchange_delete(exchange_name)
                    return await channel.declare_exchange(exchange_name, ex_type, durable=durable)
                except Exception as e:
                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 2
                        self.logger.warning(f"Attempt {attempt + 1} failed for exchange {exchange_name}. Retrying in {wait_time} seconds... Error: {type(e).__name__}: {str(e)}")
                        await asyncio.sleep(wait_time)
                        continue
                    self.logger.error(f"Failed to recreate exchange {exchange_name} after {max_retries} attempts: {type(e).__name__}: {str(e)}")
                    raise
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2
                    self.logger.warning(f"Attempt {attempt + 1} failed for exchange {exchange_name}. Retrying in {wait_time} seconds... Error: {type(e).__name__}: {str(e)}")
                    await asyncio.sleep(wait_time)
                    continue
                self.logger.error(f"Failed to declare exchange {exchange_name} after {max_retries} attempts: {type(e).__name__}: {str(e)}")
                raise

    async def setup_exchange(self, name, ex_type, durable):
        self.logger.info("Setting up RabbitMQManager: connecting and declaring exchanges...")
        connection = await self.rabbit_mq_client.get_connection()
        self.channel = await connection.channel()

        await self.channel.set_qos(prefetch_count=self.config.PREFETCH_COUNT)
        dlx_exchange_name = f"{name}{self.config.DLX_SUFFIX}"
        exchange = await self._safe_declare_exchange(name, ex_type, durable)
        dlx_exchange = await self._safe_declare_exchange(dlx_exchange_name, ex_type, durable)

        self.exchanges[name] = exchange
        self.exchanges[dlx_exchange_name] = dlx_exchange
        self.logger.info(f"Exchange {name} from {ex_type} type and {durable} durability declared and cached.")

    async def setup_dlx_queue(
        self,
        channel: Channel,
        queue_name: str,
        exchange_name: str,
        routing_key: str,
    ) -> tuple[Queue, Queue]:
        
        dlx_queue = await self._safe_declare_queue(
            channel,
            f"{queue_name}{self.config.DLX_SUFFIX}",
            durable=True,
            arguments={
                'x-message-ttl': self.config.DLX_TTL
            }
        )
        
        await dlx_queue.bind(
            self.exchanges[f"{exchange_name}{self.config.DLX_SUFFIX}"],
            routing_key=f"{routing_key}{self.config.DLX_SUFFIX}"
        )
        
        return dlx_queue

    async def setup_queue(
        self,
        channel: Channel,
        queue_name: str,
        exchange_name: str,
        routing_key: str,
    ) -> Queue:
        
        queue = await self._safe_declare_queue(
            channel,
            queue_name,
            durable=True,
            arguments={
                'x-dead-letter-exchange': f"{exchange_name}{self.config.DLX_SUFFIX}",
                'x-dead-letter-routing-key': f"{queue_name}{self.config.DLX_SUFFIX}",
                'x-message-ttl': self.config.QUEUE_TTL
            }
        )
        
        # Bind main queue to main exchange
        await queue.bind(
            self.exchanges[exchange_name],
            routing_key=routing_key
        )
        
        return queue
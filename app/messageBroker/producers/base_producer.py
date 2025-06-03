import asyncio
import json
import traceback
from abc import ABC, abstractmethod
from aio_pika import Message
from aiormq.exceptions import ChannelInvalidStateError
from app.utils.logger import LoggerManager
from app.db.events_db import EventsDB
from app.messageBroker.rabbit_mq_manager import RabbitMQManager
from app.models.message_bus_models import OutboxPublisher
from app.messageBroker.backpressure_manager import BackpressureManager
from app.db.mongo_db_client import MongoDBConnectionManager
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Dict, Any, Optional

class BaseProducer(ABC):
    def __init__(self, rabbitmq_manager: RabbitMQManager, exchange_name: str, db: MongoDBConnectionManager, routing_queue: str):
        self.logger = LoggerManager.get_logger(self.__class__.__name__)
        self.rabbitmq_manager = rabbitmq_manager
        self.exchange_name = exchange_name
        self.db: AsyncIOMotorClient = db
        self.outbox_publisher: OutboxPublisher = None
        self.events_db = EventsDB(db)
        self.routing_queue = routing_queue
        # Initialize backpressure manager
        self.backpressure_manager = BackpressureManager(
            rabbitmq_manager=self.rabbitmq_manager,
            consumer_queue_name=self.routing_queue
        )

    @abstractmethod
    def _initialize_outbox_publisher(self):
        """Initialize the outbox publisher with producer-specific configuration."""
        pass

    @abstractmethod
    def _get_event_filter(self) -> dict:
        """Returns the filter for finding unhandled and unpublished events."""
        pass

    def _serialize(self, obj):
        """Serialize an object to JSON format."""
        import datetime
        def default(o):
            if isinstance(o, (datetime.datetime, datetime.date)):
                return o.isoformat()
            return str(o)
        try:
            if hasattr(obj, 'model_dump'):
                obj = obj.model_dump()
            return json.dumps(obj, default=default)
        except Exception as e:
            self.logger.error(f"Error serializing object to JSON: {e}\n{traceback.format_exc()}")
            raise e
    
    def _create_message(self, event):
        """Create a RabbitMQ message from an event."""
        try:
            body = self._serialize(event)
            message = Message(
                body=body.encode(),
                content_type="application/json",
                delivery_mode=2,  # PERSISTENT
            )
            return message
        except Exception as e:
            self.logger.error(f"Error serializing item: {e}\n{traceback.format_exc()}")
            raise e

    async def _publish_messages(self, events, routing_key=""):
        """Publish a batch of messages to RabbitMQ with retry logic."""
        if events is None or len(events) == 0:
            self.logger.warning(f"No messages to publish in {self.__class__.__name__}")
            return
        if not isinstance(events, (list, tuple)):
            raise TypeError(f"events must be a list or tuple, got {type(events).__name__}")

        semaphore = asyncio.Semaphore(self.outbox_publisher.max_messages_to_publish)

        async def publish_with_retry(event):
            async with semaphore:
                for attempt in range(self.outbox_publisher.max_retries):
                    try:
                        exchange = self.rabbitmq_manager.exchanges.get(self.exchange_name)
                        message = self._create_message(event)
                        await exchange.publish(message, routing_key=routing_key)
                        return
                    except ChannelInvalidStateError as e:
                        self.logger.error(f"{self.__class__.__name__}[!] ChannelInvalidStateError on attempt {attempt+1}: {e}\n{traceback.format_exc()}")
                        if attempt < self.outbox_publisher.max_retries - 1:
                            await asyncio.sleep(self.outbox_publisher.initial_delay * (2 ** attempt))
                            continue
                        else:
                            raise e
                    except Exception as e:
                        self.logger.error(f"{self.__class__.__name__}[!] Error publishing message: {e}\n{traceback.format_exc()}")
                        raise e

        tasks = [publish_with_retry(event) for event in events]
        await asyncio.gather(*tasks)

    async def _publish_and_update_events(self, events: List[dict], routing_key: str) -> int:
        """
        Common method to publish events and update their status.
        Uses MongoDB transactions to ensure atomicity between publishing and updating.
        Returns the number of events that were successfully processed.
        """
        if not events:
            self.logger.info("No new events to publish.")
            return 0

        self.logger.info(f"Publishing {len(events)} events.")
        
        try:
            # First update the events as published in MongoDB
            event_ids = [event['_id'] for event in events if event.get('_id')]
            updated_count = await self.events_db.update_events_published(event_ids)
            
            # Then publish to RabbitMQ
            try:
                await self._publish_messages(events, routing_key=routing_key)
            except Exception as e:
                updated_count = await self.events_db.update_events_published(event_ids, is_published=False)
                self.logger.error(f"Failed to publish events to RabbitMQ: {e}")
                raise e
                            
            self.logger.info(f"Published and marked {updated_count} events as handled.")
            return updated_count
        except Exception as e:
            self.logger.error(f"Failed to publish and update events: {e}")
            raise e

    async def _log_backpressure_stats(self, updated_count: int):
        """Log backpressure statistics if events were published."""
        if updated_count > 0:
            stats = self.backpressure_manager.get_statistics()
            self.logger.info(f"Backpressure statistics: {stats}")

    async def _fetch_events(self) -> List[dict]:
        """Fetch events based on the producer's filter."""
        return await self.events_db.find_events_by_filter(
            self._get_event_filter(),
            limit=self.outbox_publisher.batch_size_events_query
        )

    async def run_outbox_producer(self):
        """
        Base implementation of the outbox producer loop.
        Handles fetching, publishing, and updating events with backpressure.
        """
        await asyncio.sleep(self.outbox_publisher.initial_delay)
        
        while True:
            try:
                # Apply backpressure
                await self.backpressure_manager.apply_backpressure()
                
                # Fetch events
                events = await self._fetch_events()
                
                # Publish and update events
                updated_count = await self._publish_and_update_events(events, self.routing_queue)
                await self._log_backpressure_stats(updated_count)

                await asyncio.sleep(self.outbox_publisher.retry_delay)

            except Exception as e:
                self.logger.error(f"Error in publish_new_events_batch: {e}\n{traceback.format_exc()}")
                raise e
import asyncio
import json
import traceback
from abc import ABC, abstractmethod
from aio_pika import Message, Exchange
from aiormq.exceptions import ChannelInvalidStateError
from app.utils.logger import LoggerManager
from config import get_config
from app.models.statuses_enums import EventType
from app.db.events_db import EventsDB
import os
from app.bus_messages.rabbit_mq_manager import RabbitMQManager
from app.app_container import app_container
MAX_RETRIES = 3
INITIAL_DELAY = 1

class BasePublisher(ABC):
    def __init__(self, rabbitmq_manager: RabbitMQManager, logger_name: str, exchange_name: str, db):
        self.rabbitmq_manager = rabbitmq_manager
        self.logger = LoggerManager.get_logger(logger_name)
        self.exchange_name = exchange_name
        self.events_db = EventsDB(db)

    def _serialize(self, obj):
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
        if events is None or len(events) == 0:
            self.logger.warning(f"No messages to publish. in {self.__class__.__name__}")
            return
        if not isinstance(events, (list, tuple)):
            raise TypeError(f"events must be a list or tuple, got {type(events).__name__}")
        
        for attempt in range(MAX_RETRIES):
            try:
                exchange = self.rabbitmq_manager.get_exchange(self.exchange_name)
                self.logger.info(f"Publishing {len(events)} messages to {routing_key} queue in {exchange.name} exchange")
                
                # publish messages to the exchange
                for event in events:
                    message = self._create_message(event)
                    await exchange.publish(message, routing_key=routing_key)
                
                self.logger.info(f"Published {len(events)} messages ✅")
                break
            except ChannelInvalidStateError as e:
                self.logger.error(f"{self.__class__.__name__}[!] ChannelInvalidStateError on attempt {attempt+1}: {e}\n{traceback.format_exc()}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.initial_delay * (2 ** attempt))
                    continue
                else:
                    raise e
            except Exception as e:
                self.logger.error(f"{self.__class__.__name__}[!] Error publishing messages: {e}\n{traceback.format_exc()}")
                raise e 

    async def run_outbox_publisher(self, event_type: EventType, routing_key: str):
        """
        Publishes a batch of new events of the given type that are published but not yet handled.
        Marks them as handled in the DB if successful.
        """
        max_parallel = int(os.getenv("MAX_SIMULATIONS_IN_PARALLEL", 5))
        filter = {
            "is_handled": False,
            "published": False,
            "event_type": event_type.value
        }
        while True: 
            try:
                events = await self.events_db.find_events_by_filter(filter, limit=max_parallel)
                if not events:
                    self.logger.info("No new events to publish.")
                    await asyncio.sleep(2)
                    continue
                
                self.logger.info(f"Publishing {len(events)} events.")
                
                event_ids = [e['_id'] for e in events if e['_id']]
                updated_count, updated_events = await self.events_db.update_events_published(event_ids)

                await self._publish_messages(updated_events, routing_key)
                self.logger.info(f"Published and marked {updated_count} events as handled.")
            except Exception as e:
                self.logger.error(f"Error in publish_new_events_batch: {e}\n{traceback.format_exc()}") 
                raise e
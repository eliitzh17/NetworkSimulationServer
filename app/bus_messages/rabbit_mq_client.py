import aio_pika
from app.utils.logger import LoggerManager

class RabbitMQClient:
    def __init__(self, url: str):
        self.connection = None
        self.channel = None
        self.logger = LoggerManager.get_logger('rabbit_mq_client')
        self.url = url

    async def get_connection(self):
        if self.connection is None or self.connection.is_closed:
            self.logger.info(f"Connecting to RabbitMQ at {self.url}")
            try:
                self.connection = await aio_pika.connect_robust(self.url)
                self.logger.info("Connected to RabbitMQ")
            except Exception as e:
                self.logger.error(f"Failed to connect to RabbitMQ: {e}")
                raise e
            
        return self.connection
    
    async def get_channel(self):
        if self.channel is None:
            self.logger.info("Getting channel")
            try:
                self.channel = await self.connection.channel()
                self.logger.info("Channel created")
            except Exception as e:
                self.logger.error(f"Failed to create channel: {e}")
                raise e
        return self.channel

    async def reconnect(self):
        self.logger.info("Reconnecting to RabbitMQ...")
        try:
            if self.channel is not None:
                try:
                    await self.channel.close()
                    self.logger.info("Channel closed.")
                except Exception as e:
                    self.logger.warning(f"Error closing channel: {e}")
                self.channel = None
            if self.connection is not None:
                try:
                    await self.connection.close()
                    self.logger.info("Connection closed.")
                except Exception as e:
                    self.logger.warning(f"Error closing connection: {e}")
                self.connection = None
            # Establish new connection
            await self.get_connection()
            self.logger.info("Reconnected to RabbitMQ.")
        except Exception as e:
            self.logger.error(f"Failed to reconnect to RabbitMQ: {e}")
            raise e



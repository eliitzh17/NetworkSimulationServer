from dependency_injector import containers, providers
from app.db.mongo_db_client import MongoDBConnectionManager
from app.rabbit_mq.rabbit_mq_client import RabbitMQClient
from config import get_config

class Container(containers.DeclarativeContainer):
    config = providers.Singleton(get_config)
    mongo_manager = providers.Factory(MongoDBConnectionManager)
    rabbitmq_client = providers.Factory(
        RabbitMQClient,
        url=config.provided.RABBITMQ_URL,
    )

container = Container()

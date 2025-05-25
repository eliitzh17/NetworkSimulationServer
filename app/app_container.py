from dependency_injector import containers, providers
from app.db.mongo_db_client import MongoDBConnectionManager
from app.bus_messages.rabbit_mq_client import RabbitMQClient
from config import get_config, BaseConfig

class AppContainer(containers.DeclarativeContainer):
    config: BaseConfig = providers.Singleton(get_config)
    mongo_manager = providers.Factory(MongoDBConnectionManager)
    rabbitmq_client = providers.Factory(
        RabbitMQClient,
        url=config.provided.RABBITMQ_URL,
    )

app_container = AppContainer()

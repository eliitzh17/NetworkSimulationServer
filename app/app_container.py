from dependency_injector import containers, providers
from app.db.mongo_db_client import MongoDBConnectionManager
from app.messageBroker.rabbit_mq_client import RabbitMQClient
from app.config import get_config, AppConfig

class AppContainer(containers.DeclarativeContainer):
    config: AppConfig = providers.Singleton(get_config)
    mongo_manager: MongoDBConnectionManager = providers.Factory(
        MongoDBConnectionManager,
        config=config
    )
    rabbitmq_client: RabbitMQClient = providers.Factory(
        RabbitMQClient,
        url=config.provided.RABBITMQ_URL,
    )

app_container = AppContainer()

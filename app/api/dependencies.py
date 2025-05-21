from app import container
from app.utils.logger import LoggerManager

logger = LoggerManager.get_logger('mongo_dependency')

async def get_mongo_manager(with_transaction: bool = False):
    """
    Dependency for MongoDB connection.
    If with_transaction=True, yields (db, session) and manages transaction commit/abort.
    If with_transaction=False, yields db only.
    Usage:
        db = Depends(partial(get_mongo_manager, with_transaction=False))
        db, session = Depends(partial(get_mongo_manager, with_transaction=True))
    """
    mongo_manager = container.mongo_manager()
    logger.info("MongoDB connection not established, connecting...")
    await mongo_manager.connect()
    # Connection is now managed at app startup/shutdown
    logger.info("MongoDB connection provided via dependency.")
    session = None
    if with_transaction:
        session = await mongo_manager.client.start_session()
        await session.start_transaction()
        logger.info("MongoDB session and transaction started.")
    try:
        if with_transaction:
            yield mongo_manager.db, session
        else:
            yield mongo_manager.db
        if with_transaction and session:
            await session.commit_transaction()
            logger.info("MongoDB transaction committed.")
    except Exception as e:
        if with_transaction and session:
            await session.abort_transaction()
            logger.error(f"MongoDB transaction aborted due to exception: {e}")
        raise
    finally:
        if with_transaction and session:
            await session.end_session()
            logger.info("MongoDB session ended.")
        await mongo_manager.close()
        logger.info("MongoDB connection closed via dependency.")

async def get_rabbitmq_client():
    rabbitmq_client = container.rabbitmq_client()
    try:
        yield rabbitmq_client
    finally:
        if hasattr(rabbitmq_client, 'connection') and rabbitmq_client.connection:
            if not rabbitmq_client.connection.is_closed:
                await rabbitmq_client.connection.close()
        if hasattr(rabbitmq_client, 'channel') and rabbitmq_client.channel:
            if not rabbitmq_client.channel.is_closed:
                await rabbitmq_client.channel.close() 
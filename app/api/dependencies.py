from app.app_container import app_container
from app.utils.logger import LoggerManager

logger = LoggerManager.get_logger('mongo_dependency')

async def _ensure_mongo_connected(mongo_manager):
    if not (await mongo_manager.is_connected()):
        logger.info("MongoDB connection not established, connecting...")
        await mongo_manager.connect()

async def _start_session_and_transaction(mongo_manager):
    session = await mongo_manager.client.start_session()
    session.start_transaction()
    logger.info("MongoDB session and transaction started.")
    return session

async def _commit_transaction(session):
    await session.commit_transaction()
    logger.info("MongoDB transaction committed.")

async def _abort_transaction(session, exc):
    await session.abort_transaction()
    logger.error(f"MongoDB transaction aborted due to exception: {exc}")

async def _end_session(session):
    await session.end_session()
    logger.info("MongoDB session ended.")

async def get_mongo_manager(with_transaction: bool = False):
    """
    Dependency for MongoDB connection.
    If with_transaction=True, yields (db, session) and manages transaction commit/abort.
    If with_transaction=False, yields db only.
    Usage:
        db = Depends(partial(get_mongo_manager, with_transaction=False))
        db, session = Depends(partial(get_mongo_manager, with_transaction=True))
    """
    mongo_manager = app_container.mongo_manager()
    await _ensure_mongo_connected(mongo_manager)
    session = None
    try:
        if with_transaction:
            session = await _start_session_and_transaction(mongo_manager)
            yield mongo_manager.db, session
            await _commit_transaction(session)
        else:
            yield mongo_manager.db
    except Exception as e:
        if with_transaction and session:
            await _abort_transaction(session, e)
        raise
    finally:
        if with_transaction and session:
            await _end_session(session)

async def get_mongo_read_manager():
    """
    Dependency for read-only MongoDB operations.
    Yields db only, no transaction support.
    Usage:
        db = Depends(get_mongo_read_manager)
    """
    mongo_manager = app_container.mongo_manager()
    await _ensure_mongo_connected(mongo_manager)
    yield mongo_manager.db

async def get_rabbitmq_client():
    rabbitmq_client = app_container.rabbitmq_client()
    try:
        yield rabbitmq_client
    finally:
        if hasattr(rabbitmq_client, 'connection') and rabbitmq_client.connection:
            if not rabbitmq_client.connection.is_closed:
                await rabbitmq_client.connection.close()
        if hasattr(rabbitmq_client, 'channel') and rabbitmq_client.channel:
            if not rabbitmq_client.channel.is_closed:
                await rabbitmq_client.channel.close() 
from app.rabbit_mq.consumers.link_post_run_consumer import LinkPostRunConsumer
from app.workers.base_worker import run_worker
import asyncio

if __name__ == "__main__":
    asyncio.run(run_worker(
        consumer_class=LinkPostRunConsumer,
        logger_name="handle_in_post_link_worker"
    )) 
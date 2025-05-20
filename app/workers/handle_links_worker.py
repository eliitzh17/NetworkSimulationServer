from app.rabbit_mq.consumers.run_links_consumer import LinksConsumer
from app.workers.base_worker import run_worker
import asyncio

if __name__ == "__main__":
    asyncio.run(run_worker(
        consumer_class=LinksConsumer,
        logger_name="handle_links_worker",
        consumer_args={"port": 9092}
    )) 
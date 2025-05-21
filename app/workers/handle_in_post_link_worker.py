from fastapi import FastAPI
import asyncio
from app.workers.base_worker import run_worker
from app.rabbit_mq.consumers.link_post_run_consumer import LinkPostRunConsumer
import uvicorn
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app):
    asyncio.create_task(run_worker(
        consumer_class=LinkPostRunConsumer,
        logger_name="handle_in_post_link_worker"
    ))
    yield

app = FastAPI(lifespan=lifespan)

@app.get("/health")
def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run("app.workers.handle_in_post_link_worker:app", host="0.0.0.0", port=6000, log_level="info") 
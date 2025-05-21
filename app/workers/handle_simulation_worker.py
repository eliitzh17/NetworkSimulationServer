from fastapi import FastAPI
import asyncio
from app.workers.base_worker import run_worker
from app.rabbit_mq.consumers.simulations_consumer import SimulationConsumer
import uvicorn
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app):
    asyncio.create_task(run_worker(
        consumer_class=SimulationConsumer,
        logger_name="handle_simulation_worker"
    ))
    yield

app = FastAPI(lifespan=lifespan)

@app.get("/health")
def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run("app.workers.handle_simulation_worker:app", host="0.0.0.0", port=8001, log_level="info") 
from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.api.simulation_creator_api import simulation_creator_router
from app.api.simulation_management_api import simulation_management_router
from app.utils.logger import LoggerManager
from fastapi.middleware.cors import CORSMiddleware
from app.api.simulation_data_api import simulation_data_router
from app.api.debug_api import debug_router
from app import container

main_logger = LoggerManager.get_logger('main')
mongo_manager = container.mongo_manager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        config = container.config()
        main_logger.info("Starting application...")
        await mongo_manager.connect()
        await mongo_manager.ensure_indexes()
        app.state.db = mongo_manager.db
        main_logger.info("MongoDB connected and repository initialized.")
        yield
    finally:
        try:
            main_logger.info("Shutting down application...")
            await mongo_manager.close()
            main_logger.info("MongoDB connection closed.")
        except Exception as e:
            main_logger.error(f"Error during shutdown: {str(e)}")

# app = FastAPI(lifespan=lifespan)

app = FastAPI(
    title="Simulation API",
    description="API for managing simulations",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include our endpoints
base_path = "/api"
app.include_router(simulation_creator_router, prefix=base_path)
app.include_router(simulation_management_router, prefix=base_path)
app.include_router(simulation_data_router, prefix=base_path)
app.include_router(debug_router, prefix=base_path)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"} 


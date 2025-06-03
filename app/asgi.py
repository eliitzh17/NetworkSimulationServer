from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.api.simulation_creator_api import simulation_creator_router
from app.api.simulation_management_api import simulation_management_router
from app.api.simulation_data_api import simulation_data_router
from app.api.debug_api import debug_router
from app.app_container import app_container
from app.utils.logger import LoggerManager

main_logger = LoggerManager.get_logger('Api ASGI')

class Application:
    def __init__(self):
        self.config = app_container.config()
        self.mongo_manager = app_container.mongo_manager()

    @asynccontextmanager
    async def lifespan(self, app: FastAPI):
        try:
            main_logger.info("Starting application...")
            await self.mongo_manager.connect()
            await self.mongo_manager.ensure_indexes()
            app.state.db = self.mongo_manager.db
            main_logger.info("MongoDB connected and repository initialized.")
            yield
        finally:
            try:
                main_logger.info("Shutting down application...")
                await self.mongo_manager.close()
                main_logger.info("MongoDB connection closed.")
            except Exception as e:
                main_logger.error(f"Error during shutdown: {str(e)}")

    def create_app(self) -> FastAPI:
        app = FastAPI(lifespan=self.lifespan)
        
        # Add CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Include routers
        app.include_router(simulation_creator_router, prefix="/api/v1")
        app.include_router(simulation_management_router, prefix="/api/v1")
        app.include_router(simulation_data_router, prefix="/api/v1")
        app.include_router(debug_router, prefix="/api/v1/debug")
        
        return app

# Create application instance
app = Application().create_app()
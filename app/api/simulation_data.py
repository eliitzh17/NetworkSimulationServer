from app.utils.logger import LoggerManager
from fastapi import APIRouter, Request
from typing import List

logger = LoggerManager.get_logger("simulation_data")
simulation_data_router = APIRouter()
simulation_data_router = APIRouter(prefix="/simulation-data", tags=["simulation_data"])

@simulation_data_router.get("/status/{simulation_id}", summary="Get a simulation status", tags=["simulation_data"])
async def get_simulation_status(simulation_id: str) -> str:
    logger.info(f"Will get simulation {simulation_id} status")

@simulation_data_router.get("/{simulation_id}", summary="Get a simulation", tags=["simulation_data"])
async def get_simulation(simulation_id: str) -> str:
    logger.info(f"Will get simulation {simulation_id} status")
    
@simulation_data_router.get("/meta-data/{simulation_id}", summary="Get a simulation meta data", tags=["simulation_data"])
async def get_simulation_meta_data(simulation_id: str) -> str:
    logger.info(f"Will get simulation {simulation_id} status")
    
    
@simulation_data_router.get("/get-all-simulations-in-status/{status}", summary="Get all new simulations")
async def get_all_new_simulations(status: str, request: Request) -> List[str]:
    logger.info("Will get all new simulations")
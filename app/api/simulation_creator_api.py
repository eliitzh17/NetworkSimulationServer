from fastapi import APIRouter
from app.utils.logger import LoggerManager
from app.models.requests_models import SimulationRequest
from typing import List
from app.models.mapper import SimulationMapper
from app.core.simulation_bl import SimulationBusinessLogic
import asyncio
from fastapi import APIRouter, Request

logger = LoggerManager.get_logger("simulation_creator_api")

simulation_creator_router = APIRouter()

logger.info("simulation_creator_api router initialized")

@simulation_creator_router.post("/simulate", summary="Create a new simulation/s")
async def create_simulation(requests: List[SimulationRequest], request: Request) -> List[str]:
    simulations = [SimulationMapper.request_to_simulation(request) for request in requests]
    logger.info(f"Will create {len(simulations)} simulations")
    
    simulation_manager = SimulationBusinessLogic(request.app.state.db)
    await asyncio.gather(*(simulation_manager.publish_new_simulation(simulation) for simulation in simulations))
    
    return [simulation.sim_id for simulation in simulations]
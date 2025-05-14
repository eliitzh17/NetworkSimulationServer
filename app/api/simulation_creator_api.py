from fastapi import APIRouter, Depends
from app.utils.logger import LoggerManager
from app.models.requests_models import SimulationRequest
from typing import List
from app.models.mapper import SimulationMapper
from app.core.simulation_bl import SimulationBusinessLogic
import asyncio
from fastapi import APIRouter, Request
from app import container
from contextlib import asynccontextmanager
from app.api.dependencies import get_mongo_manager, get_rabbitmq_client

logger = LoggerManager.get_logger("simulation_creator_api")

simulation_creator_router = APIRouter()

logger.info("simulation_creator_api router initialized")

@simulation_creator_router.post("/simulate", summary="Create a new simulation/s", tags=["Simulation"])
async def create_simulation(
    requests: List[SimulationRequest],
    db=Depends(get_mongo_manager),
    rabbitmq_client=Depends(get_rabbitmq_client),
) -> List[str]:
    
    simulations = [SimulationMapper.request_to_simulation(request) for request in requests]
    logger.info(f"Will create {len(simulations)} simulations")
    
    #TODO: transactions against db and message queue should be bulk
    simulation_manager = SimulationBusinessLogic(db, rabbitmq_client)
    await asyncio.gather(*(simulation_manager.publish_new_simulation(simulation) for simulation in simulations))
    
    return [simulation.sim_id for simulation in simulations]
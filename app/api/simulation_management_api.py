from app.models.requests_models import SimulationRequest
from app.models.mapper import SimulationMapper
from app.core.simulation_bl import SimulationBusinessLogic
from app.utils.logger import LoggerManager
from fastapi import APIRouter, Request
from typing import List

logger = LoggerManager.get_logger("simulation_management_api")

simulation_management_router = APIRouter()

logger.info("simulation_management_api router initialized")

@simulation_management_router.post("/restart/{simulation_id}", summary="Restart a simulation", tags=["simulation_management"])
async def restart_simulation(simulation_id: str, request: Request) -> str:
    simulation_manager = SimulationBusinessLogic(request.app.state.db)
    await simulation_manager.run_simulation(simulation_id)
    logger.info(f"Will run simulation {simulation_id}")
    return {"message": f"Simulation {simulation_id} re-run successfully"}
    
@simulation_management_router.post("/pause/{simulation_id}", summary="Pause a simulation", tags=["simulation_management"])
async def pause_simulation(simulation_id: str, request: Request) -> str:
    logger.info(f"Will pause simulation {simulation_id}")
    
@simulation_management_router.post("/stop/{simulation_id}", summary="Stop a simulation manually", tags=["simulation_management"])
async def stop_simulation_manually(simulation_id: str, request: Request) -> str:
    logger.info(f"Will stop simulation {simulation_id} manually")
    
@simulation_management_router.put("/edit/{simulation_id}", summary="Edit a simulation", tags=["simulation_management"])
async def edit_simulation(simulation_id: str) -> str:
    logger.info(f"Will edit simulation {simulation_id}")

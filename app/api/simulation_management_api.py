from app.utils.logger import LoggerManager
from fastapi import APIRouter, Depends
from app.api.dependencies import get_mongo_manager
from app.business_logic.topologies_simulation_bl import TopologiesSimulationsBusinessLogic     
from functools import partial
from app.api.api_error_handler import handle_api_exceptions
from app.db.topologies_simulations_db import TopologiesSimulationsDB
from app.business_logic.exceptions import ValidationError
from app.business_logic.topologies_actions_bl import SimulationActionsBL
from app.api.api_utils import get_simulation_or_raise
from typing import Annotated, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.client_session import ClientSession
logger = LoggerManager.get_logger("simulation_management_api")

simulation_management_router = APIRouter()

logger.info("simulation_management_api router initialized")

def get_db_with_transaction():
    return partial(get_mongo_manager, with_transaction=True)

@simulation_management_router.post("/restart/{simulation_id}", summary="Restart a simulation", tags=["simulation_management"])
@handle_api_exceptions
async def restart_simulation(
    simulation_id: str,
    db_session: Annotated[Tuple[AsyncIOMotorDatabase, ClientSession], Depends(get_db_with_transaction())]
) -> str:
    db, session = db_session
    simulation = await get_simulation_or_raise(db, simulation_id, session)
    
    simulation_actions_bl = SimulationActionsBL(db)
    await simulation_actions_bl.restart_simulation(simulation, session=session)
    logger.info(f"Will run simulation {simulation_id}")
    return {"message": f"Simulation {simulation_id} re-run successfully"}
    
@simulation_management_router.post("/pause/{simulation_id}", summary="Pause a simulation", tags=["simulation_management"])
@handle_api_exceptions
async def pause_simulation(
    simulation_id: str, 
    db_session: Annotated[Tuple[AsyncIOMotorDatabase, ClientSession], Depends(get_db_with_transaction())]
) -> str:
    db, session = db_session
    simulation = await get_simulation_or_raise(db, simulation_id, session)
    
    simulation_actions_bl = SimulationActionsBL(db)
    result = await simulation_actions_bl.pause_simulation(simulation, session=session)
    return result

@simulation_management_router.post("/resume/{simulation_id}", summary="Resume a simulation", tags=["simulation_management"])
@handle_api_exceptions
async def resume_simulation(
    simulation_id: str, 
    db_session: Annotated[Tuple[AsyncIOMotorDatabase, ClientSession], Depends(get_db_with_transaction())]
) -> str:
    db, session = db_session
    simulation = await get_simulation_or_raise(db, simulation_id, session)
    
    simulation_actions_bl = SimulationActionsBL(db)
    result = await simulation_actions_bl.resume_simulation(simulation, session=session)
    return result
    
@simulation_management_router.put("/edit/{simulation_id}", summary="Edit a simulation", tags=["simulation_management"])
@handle_api_exceptions
async def edit_simulation(
    simulation_id: str, 
    db_session: Annotated[Tuple[AsyncIOMotorDatabase, ClientSession], Depends(get_db_with_transaction())]
) -> str:
    db, session = db_session
    simulation = await get_simulation_or_raise(db, simulation_id, session)
    
    simulation_actions_bl = SimulationActionsBL(db)
    await simulation_actions_bl.edit_simulation(simulation, session=session)
    logger.info(f"Will edit simulation {simulation_id}")
    return {"message": f"Simulation {simulation_id} edited successfully"}

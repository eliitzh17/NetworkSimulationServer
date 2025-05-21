from app.utils.logger import LoggerManager
from fastapi import APIRouter, Depends, Query
from typing import List
from app.db.simulation_db import SimulationDB
from app.models.simulation_models import Simulation, SimulationMetaData, PaginationResponse, CursorPaginationResponse
from app.models.statuses_enums import TopologyStatusEnum
from app.db.simulation_meta_data_db import SimulationMetaDataDB
from app.api.dependencies import get_mongo_manager
from app.models.requests_models import PaginationRequest, CursorPaginationRequest

logger = LoggerManager.get_logger("simulation_data")
simulation_data_router = APIRouter()
simulation_data_router = APIRouter(prefix="/simulation-data", tags=["simulation_data"])

@simulation_data_router.get("/status/{simulation_id}", summary="Get a simulation status", tags=["simulation_data"])
async def get_simulation_status(simulation_id: str, db=Depends(get_mongo_manager)) -> TopologyStatusEnum:
    """
    Get the current status of a simulation by its ID.
    Returns the status as a TopologyStatusEnum.
    """
    logger.info(f"Will get simulation {simulation_id} status")
    simulation_db = SimulationDB(db)
    simulation = await simulation_db.get_simulation(simulation_id)
    return simulation.status

@simulation_data_router.get("/get-simulation/{simulation_id}", summary="Get a simulation", tags=["simulation_data"])
async def get_simulation(simulation_id: str, db=Depends(get_mongo_manager)) -> Simulation:
    """
    Retrieve the full simulation object by its ID.
    Returns a Simulation model with all details.
    """
    logger.info(f"Will get simulation {simulation_id}")
    simulation_db = SimulationDB(db)
    simulation = await simulation_db.get_simulation(simulation_id)
    return simulation
    
@simulation_data_router.get("/get-simulation-meta-data/{simulation_id}", summary="Get a simulation meta data", tags=["simulation_data"])
async def get_simulation_meta_data(simulation_id: str, db=Depends(get_mongo_manager)) -> SimulationMetaData:
    """
    Retrieve the meta data for a simulation by its ID.
    Returns a SimulationMetaData model with execution and machine info.
    """
    logger.info(f"Will get simulation {simulation_id} meta data")
    simulation_meta_data_db = SimulationMetaDataDB(db)
    meta_data = await simulation_meta_data_db.get_by_sim_id(simulation_id)
    return meta_data

@simulation_data_router.get("/get-all-simulations-cursor", summary="Get all simulations (cursor-based)", response_model=CursorPaginationResponse)
async def get_all_simulations_cursor(
    cursor: str = Query(None, description="MongoDB ObjectId to start after"),
    page_size: int = Query(10, ge=1, le=100),
    with_total: bool = Query(False, description="Whether to include total count"),
    db=Depends(get_mongo_manager)
) -> CursorPaginationResponse:
    """
    Get a cursor-paginated list of all simulations.
    Returns a CursorPaginationResponse containing a list of Simulation objects, next_cursor, and pagination metadata.
    """
    logger.info(f"Will get all simulations (cursor={cursor}, page_size={page_size}, with_total={with_total})")
    simulation_db = SimulationDB(db)
    req = CursorPaginationRequest(cursor=cursor, page_size=page_size, with_total=with_total)
    return await simulation_db.list_all_cursor(req)

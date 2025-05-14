from app.utils.logger import LoggerManager
from fastapi import APIRouter, Depends
from typing import List
from app.db.simulation_db import SimulationDB
from app.models.simulation_models import Simulation, SimulationMetaData
from app.models.statuses_enums import TopologyStatusEnum
from app.db.simulation_meta_data_db import SimulationMetaDataDB
from app.api.dependencies import get_mongo_manager

logger = LoggerManager.get_logger("simulation_data")
simulation_data_router = APIRouter()
simulation_data_router = APIRouter(prefix="/simulation-data", tags=["simulation_data"])

@simulation_data_router.get("/status/{simulation_id}", summary="Get a simulation status", tags=["simulation_data"])
async def get_simulation_status(simulation_id: str, db=Depends(get_mongo_manager)) -> TopologyStatusEnum:
    logger.info(f"Will get simulation {simulation_id} status")
    simulation_db = SimulationDB(db)
    simulation = await simulation_db.get_simulation(simulation_id)
    return simulation.status

@simulation_data_router.get("/get-simulation/{simulation_id}", summary="Get a simulation", tags=["simulation_data"])
async def get_simulation(simulation_id: str, db=Depends(get_mongo_manager)) -> Simulation:
    logger.info(f"Will get simulation {simulation_id}")
    simulation_db = SimulationDB(db)
    simulation = await simulation_db.get_simulation(simulation_id)
    return simulation
    
@simulation_data_router.get("/get-simulation-meta-data/{simulation_id}", summary="Get a simulation meta data", tags=["simulation_data"])
async def get_simulation_meta_data(simulation_id: str, db=Depends(get_mongo_manager)) -> SimulationMetaData:
    logger.info(f"Will get simulation {simulation_id} meta data")
    simulation_meta_data_db = SimulationMetaDataDB(db)
    meta_data = await simulation_meta_data_db.get_by_sim_id(simulation_id)
    return meta_data
    
@simulation_data_router.get("/get-all-simulations", summary="Get all simulations")
async def get_all_simulations(db=Depends(get_mongo_manager)) -> List[Simulation]:
    logger.info("Will get all simulations")
    simulation_db = SimulationDB(db)
    simulations = await simulation_db.list_all()
    return simulations

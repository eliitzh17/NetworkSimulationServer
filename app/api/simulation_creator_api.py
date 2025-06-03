from fastapi import APIRouter, Depends
from app.utils.logger import LoggerManager
from app.models.requests_models import SimulationRequest
from typing import List, Annotated, Tuple
from app.api.dependencies import get_mongo_manager
from app.business_logic.topologies_bl import TopologiesBL
from functools import partial
from app.api.api_error_handler import handle_api_exceptions
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.client_session import ClientSession

logger = LoggerManager.get_logger("simulation_creator_api")

simulation_creator_router = APIRouter()

logger.info("simulation_creator_api router initialized")

def get_db_with_transaction():
    return partial(get_mongo_manager, with_transaction=True)

@simulation_creator_router.post("/simulate", summary="Create a new simulation/s", tags=["Simulation"])
@handle_api_exceptions
async def create_simulation(
    requests: List[SimulationRequest],
    db_session: Annotated[Tuple[AsyncIOMotorDatabase, ClientSession], Depends(get_db_with_transaction())]
) -> List[str]:
    db, session = db_session
    topologies_bl = TopologiesBL(db)
    return await topologies_bl.trigger_simulation(requests, session=session)
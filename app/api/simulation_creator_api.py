from fastapi import APIRouter, Depends
from app.utils.logger import LoggerManager
from app.models.requests_models import SimulationRequest
from typing import List
from app.api.dependencies import get_mongo_manager
from app.core.topologies_bl import TopologiesBL
from functools import partial

logger = LoggerManager.get_logger("simulation_creator_api")

simulation_creator_router = APIRouter()

logger.info("simulation_creator_api router initialized")

@simulation_creator_router.post("/simulate", summary="Create a new simulation/s", tags=["Simulation"])
async def create_simulation(
    requests: List[SimulationRequest],
    db_session=Depends(partial(get_mongo_manager, with_transaction=True)),
) -> List[str]:
    try:
        db, session = db_session
        topologies_bl = TopologiesBL(db)
        return await topologies_bl.trigger_simulation(requests, session=session)
    except Exception as e:
        logger.error(f"Error triggering simulations: {e}")
        raise e
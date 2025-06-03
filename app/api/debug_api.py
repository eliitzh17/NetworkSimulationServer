from app.models.requests_models import SimulationRequest
from app.models.mapper import SimulationMapper
from app.messageBroker.producers.links_producer import LinksProducer
from app.business_logic.topologies_simulation_bl import TopologiesSimulationsBusinessLogic
from app.utils.logger import LoggerManager
from fastapi import APIRouter, Depends
from app.api.dependencies import get_mongo_manager, get_rabbitmq_client
from app.models.topolgy_models import Link
from app.api.api_error_handler import handle_api_exceptions

logger = LoggerManager.get_logger('debug_api')
simulation_creator_router = APIRouter()
debug_router = APIRouter(prefix="/debug", tags=["debug"])

@debug_router.post("/send-simulation-message", summary="Send a simulation message", tags=["debug"])
@handle_api_exceptions
async def send_simulation_message(
    simulation_request: SimulationRequest,
    db=Depends(get_mongo_manager),
) -> str:
    logger.info(f"Will send simulation message")
    
    simulation = SimulationMapper.request_to_simulation(simulation_request)
    topologies_simulations_bl = TopologiesSimulationsBusinessLogic(db)
    await topologies_simulations_bl.new_simulation_bl(simulation)
    
    return simulation.sim_id

@debug_router.post("/send-link-message", summary="Send a link message", tags=["debug"])
@handle_api_exceptions
async def send_link_message(
    link: Link,
    rabbitmq_client=Depends(get_rabbitmq_client),
) -> str:
    logger.info(f"Will send link message")
    
    link_publisher = LinksProducer(rabbitmq_client)
    await link_publisher.publish_run_links_messages([link])
    
    return "Link message sent"

@debug_router.get("/ping", summary="Health check for debug API", tags=["debug"])
@handle_api_exceptions
async def ping():
    """Health check endpoint for debug API."""
    logger.info("/debug/ping endpoint called")
    return {"message": "Debug API is alive"}
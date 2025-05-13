from app.models.requests_models import SimulationRequest
from app.models.simulation_models import LinkBusMessage
from app.models.mapper import SimulationMapper
from app.rabbit_mq.publishers.links_publisher import LinksPublisher
from app.core.simulation_bl import SimulationBusinessLogic
from app.utils.logger import LoggerManager
from fastapi import APIRouter, Request

logger = LoggerManager.get_logger('debug_api')
simulation_creator_router = APIRouter()
debug_router = APIRouter(prefix="/debug", tags=["debug"])

@debug_router.post("/send-simulation-message", summary="Send a simulation message", tags=["debug"])
async def send_simulation_message(simulation_request: SimulationRequest, request: Request) -> str:
    logger.info(f"Will send simulation message")
    
    simulation = SimulationMapper.request_to_simulation(simulation_request)
    simulation_manager = SimulationBusinessLogic(request.app.state.db)
    await simulation_manager.publish_new_simulation(simulation)
    
    return simulation.sim_id

@debug_router.post("/send-link-message", summary="Send a link message", tags=["debug"])
async def send_link_message(link: LinkBusMessage, request: Request) -> str:
    logger.info(f"Will send link message")
    
    link_publisher = LinksPublisher(request.app.state.rabbit_mq_client)
    await link_publisher.publish_links_messages([link])
    
    return "Link message sent"

@debug_router.get("/ping", summary="Health check for debug API")
async def ping():
    """Health check endpoint for debug API."""
    logger.info("/debug/ping endpoint called")
    return {"message": "Debug API is alive"}
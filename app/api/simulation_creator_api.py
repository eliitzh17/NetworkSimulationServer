from fastapi import APIRouter
from app.utils.logger import LoggerManager
from app.models.requests_models import SimulationRequest
from typing import List
from app.models.mapper import SimulationMapper
from app.core.simulation_bl import SimulationBusinessLogic
import asyncio
from fastapi import APIRouter, Request
from app.models.simulation_models import LinkBusMessage
from app.rabbit_mq.publishers.links_publisher import LinksPublisher
logger = LoggerManager.get_logger("simulation_creator_api")

simulation_creator_router = APIRouter()

logger.info("simulation_creator_api router initialized")

@simulation_creator_router.post("/create-simulations", summary="Create a new simulations")
async def create_simulation(requests: List[SimulationRequest], request: Request) -> List[str]:
    simulations = [SimulationMapper.request_to_simulation(request) for request in requests]
    logger.info(f"Will create {len(simulations)} simulations")
    
    simulation_manager = SimulationBusinessLogic(request.app.state.db)
    await asyncio.gather(*(simulation_manager.publish_new_simulation(simulation) for simulation in simulations))
    
    return [simulation.sim_id for simulation in simulations]

@simulation_creator_router.post("/send-simulation-message", summary="Send a simulation message")
async def send_simulation_message(simulation_request: SimulationRequest, request: Request) -> str:
    logger.info(f"Will send simulation message")
    
    simulation = SimulationMapper.request_to_simulation(simulation_request)
    simulation_manager = SimulationBusinessLogic(request.app.state.db)
    await simulation_manager.publish_new_simulation(simulation)
    
    return simulation.sim_id

@simulation_creator_router.post("/send-link-message", summary="Send a link message")
async def send_link_message(link: LinkBusMessage, request: Request) -> str:
    logger.info(f"Will send link message")
    
    link_publisher = LinksPublisher(request.app.state.rabbit_mq_client)
    await link_publisher.publish_links_messages([link])
    
    return "Link message sent"

# Example placeholder endpoint (remove or replace with real logic)
@simulation_creator_router.get("/ping", summary="Health check for creator API")
async def ping():
    """Health check endpoint for creator API."""
    logger.info("/creator/ping endpoint called")
    return {"message": "Creator API is alive"}

# Future: Import and use Pydantic models for request/response validation
# from app.models.creator import CreatorModel

# Future: Add dependencies for authentication, DB, etc.
# from fastapi import Depends

# from app.utils.logger import LoggerManager
# from fastapi import APIRouter, Request, Depends
# from app.api.dependencies import get_mongo_manager
# from app.core.topologies_simulation_bl import TopologiesSimulationsBusinessLogic     

# logger = LoggerManager.get_logger("simulation_management_api")

# simulation_management_router = APIRouter()

# logger.info("simulation_management_api router initialized")

# @simulation_management_router.post("/restart/{simulation_id}", summary="Restart a simulation", tags=["simulation_management"])
# async def restart_simulation(
#     simulation_id: str,
#     db=Depends(get_mongo_manager),
# ) -> str:
#     topologies_simulations_bl = TopologiesSimulationsBusinessLogic(db)
#     await topologies_simulations_bl.restart_simulation(simulation_id)
#     logger.info(f"Will run simulation {simulation_id}")
#     return {"message": f"Simulation {simulation_id} re-run successfully"}
    
# @simulation_management_router.post("/pause/{simulation_id}", summary="Pause a simulation", tags=["simulation_management"])
# async def pause_simulation(simulation_id: str, request: Request, db=Depends(get_mongo_manager)) -> str:
#     topologies_simulations_bl = TopologiesSimulationsBusinessLogic(db)
#     await topologies_simulations_bl.pause_simulation(simulation_id)
#     logger.info(f"Will pause simulation {simulation_id}")
#     return {"message": f"Simulation {simulation_id} paused successfully"}
    
# @simulation_management_router.post("/stop/{simulation_id}", summary="Stop a simulation manually", tags=["simulation_management"])
# async def stop_simulation_manually(simulation_id: str, request: Request, db=Depends(get_mongo_manager)) -> str:
#     topologies_simulations_bl = TopologiesSimulationsBusinessLogic(db)
#     await topologies_simulations_bl.pause_simulation(simulation_id)
#     logger.info(f"Will stop simulation {simulation_id} manually")
#     return {"message": f"Simulation {simulation_id} stopped successfully"}
    
# @simulation_management_router.put("/edit/{simulation_id}", summary="Edit a simulation", tags=["simulation_management"])
# async def edit_simulation(simulation_id: str) -> str:
#     logger.info(f"Will edit simulation {simulation_id}")

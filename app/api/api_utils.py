"""
API utilities for common operations across API endpoints.
"""
from fastapi import HTTPException
from app.db.topologies_simulations_db import TopologiesSimulationsDB
from app.models.topolgy_simulation_models import TopologySimulation

async def get_simulation_or_raise(db, simulation_id: str, session=None) -> TopologySimulation:
    """
    Get a simulation by ID or raise a 404 HTTP exception if not found.
    
    Args:
        db: Database connection
        simulation_id: ID of the simulation to retrieve
        session: Optional database session
        
    Returns:
        TopologySimulation: The found simulation
        
    Raises:
        HTTPException: 404 if simulation is not found
    """
    topologies_simulations_db = TopologiesSimulationsDB(db)
    simulation = await topologies_simulations_db.get_topology_simulation(simulation_id, session=session)
    if simulation is None:
        raise HTTPException(status_code=404, detail=f"Simulation with ID {simulation_id} not found")
    return simulation 
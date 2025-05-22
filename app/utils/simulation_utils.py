from datetime import datetime
from app.models.topolgy_simulation_models import SimulationMetaData, TopologySimulation
from app.utils.system_info import get_system_info
from app.utils.logger import LoggerManager

# Initialize logger
logger = LoggerManager.get_logger('simulation_utils')

@staticmethod
def create_simulation_metadata(sim_id: str) -> SimulationMetaData:
    # Get system information
    system_info = get_system_info()
    
    # Create metadata object
    metadata = SimulationMetaData(
        sim_id=sim_id,
        start_time=None,
        end_time=None,
        current_time=None,
        total_execution_time=0,
        processed_links=0,
        failed_links=0,
        success_links=0,
        os=system_info["os"],
        machine_id=system_info["machine_id"],
        machine_name=system_info["machine_name"],
        machine_ip=system_info["machine_ip"],
        machine_port=system_info["machine_port"],
    )
    
    logger.info(f"Created simulation metadata for sim_id={sim_id}, "
                f"machine={system_info['machine_name']}")
    
    return metadata 
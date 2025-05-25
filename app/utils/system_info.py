import socket
import uuid
import platform
import os
from typing import Dict, Tuple
from app.utils.logger import LoggerManager
from app.app_container import app_container
# Initialize logger
logger = LoggerManager.get_logger('system_info')

def get_system_info() -> Dict[str, str]:
    """
    Gets system information required for simulation metadata.
    
    Returns:
        Dict containing machine_id, machine_name, machine_ip, and machine_port
    """
    try:
        hostname = socket.gethostname()
        
        # Generate a stable machine ID based on hostname and other system info
        # This ensures the ID remains consistent across restarts
        machine_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, 
                                   f"{hostname}:{platform.node()}:{platform.machine()}"))
        
        # Get IP address
        try:
            # Try to get the non-loopback IP address
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # Doesn't need to be reachable, just to determine interface IP
            s.connect(('8.8.8.8', 1))
            machine_ip = s.getsockname()[0]
            s.close()
        except Exception:
            # Fallback to localhost if unable to determine IP
            machine_ip = socket.gethostbyname(hostname)
            
        # Try to get port from environment variables or configuration
        try:
            # Check environment variables for port
            port_value = os.getenv("SERVER_PORT") or os.getenv("API_PORT") or os.getenv("PORT")
            machine_port = int(port_value) if port_value else app_container.config().PORT
        except (ValueError, TypeError):
            # Fallback to default port
            machine_port = app_container.config().PORT
        
        logger.info(f"Retrieved system info: machine_id={machine_id}, hostname={hostname}, ip={machine_ip}, port={machine_port}")
        
        return {
            "os": platform.system(),
            "machine_id": machine_id,
            "machine_name": hostname,
            "machine_ip": machine_ip,
            "machine_port": machine_port
        }
        
    except Exception as e:
        logger.error(f"Error retrieving system information: {str(e)}")
        # Provide fallback values to prevent system failure
        return {
            "os": platform.system(),
            "machine_id": str(uuid.uuid4()),
            "machine_name": "unknown_host",
            "machine_ip": "127.0.0.1",
            "machine_port": 8000
        }

def get_network_interfaces() -> Dict[str, Tuple[str, str]]:
    """
    Gets all available network interfaces and their IP addresses.
    
    Returns:
        Dictionary mapping interface names to tuples of (ip_address, mac_address)
    """
    try:
        interfaces = {}
        for interface, addresses in socket.getaddrinfo(socket.gethostname(), None):
            if interface == socket.AF_INET:  # Only get IPv4 addresses
                ip = addresses[0]
                if ip != '127.0.0.1':
                    interfaces[addresses[-1]] = (ip, "00:00:00:00:00:00")  # MAC not easily accessible in Python
        
        return interfaces
    except Exception as e:
        logger.error(f"Error retrieving network interfaces: {str(e)}")
        return {} 
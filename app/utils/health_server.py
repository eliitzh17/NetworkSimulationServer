from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn
import threading
import socket

app = FastAPI(
    title="Simulation worker health check",
    description="Health check for simulation workers",
    version="1.0.0",
)

@app.get("/health")
def health_check():
    return JSONResponse(content={"status": "ok"})

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def start_health_server(port: int = 8000, host: str = "auto"):
    def run():
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")
    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    if host == "auto":
        host_for_url = get_local_ip()
    else:
        host_for_url = host
    return f"http://{host_for_url}:{port}/health" 
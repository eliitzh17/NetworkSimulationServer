from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn
import threading

app = FastAPI(
    title="Simulation worker health check",
    description="Health check for simulation workers",
    version="1.0.0",
)

@app.get("/health")
def health_check():
    return JSONResponse(content={"status": "ok"})

def start_health_server(port: int = 8000):
    def run():
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")
    thread = threading.Thread(target=run, daemon=True)
    thread.start() 
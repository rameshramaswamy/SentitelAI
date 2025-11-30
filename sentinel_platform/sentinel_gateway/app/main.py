import sys
from fastapi import FastAPI
from app.api.v1.endpoints import websocket
import uvicorn
from prometheus_fastapi_instrumentator import Instrumentator

# OPTIMIZATION: Use uvloop for 2-4x throughput increase (Linux/Mac only)
if sys.platform != "win32":
    import uvloop
    import asyncio
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


app = FastAPI(title="Sentinel Gateway", version="0.1.0")
instrumentator = Instrumentator().instrument(app)
# Include the WebSocket router
app.include_router(websocket.router)

@app.on_event("startup")
async def _startup():
    instrumentator.expose(app)

# Custom Metric: Track Active Websockets
from prometheus_client import Gauge
ACTIVE_CONNECTIONS = Gauge('ws_active_connections', 'Number of active WebSocket sessions')

@app.get("/health")
def health_check():
    return {"status": "ok", "engine": "uvloop" if 'uvloop' in sys.modules else "asyncio"}
import asyncio
import logging
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import orjson
from prometheus_client import Gauge

from sentinel_shared.schemas.events import (
    HandshakePayload,
    HandshakeAckPayload,
    EventType,
    OverlayTriggerPayload
)
from sentinel_shared.utils.logger import setup_logger
from app.adapters.nats_adapter import NatsAdapter

# --- Configuration & Metrics ---
router = APIRouter()
logger = setup_logger("gateway.websocket")

# Prometheus Metric: Track active connections
ACTIVE_CONNECTIONS = Gauge('ws_active_connections', 'Number of active WebSocket sessions')

# Initialize NATS Adapter (Singleton behavior via module import)
# In a larger app, use Dependency Injection (Depends(get_bus))
bus = NatsAdapter()

@router.on_event("startup")
async def startup_event():
    """Ensure NATS is connected when API starts."""
    try:
        await bus.connect()
    except Exception as e:
        logger.error(f"Failed to connect to NATS on startup: {e}")

@router.websocket("/ws/stream")
async def websocket_endpoint(websocket: WebSocket):
    """
    Main Ingress Endpoint.
    1. Handshake (Auth)
    2. NATS Subscription (Backend -> Client)
    3. Audio Stream Loop (Client -> Backend)
    """
    await websocket.accept()
    ACTIVE_CONNECTIONS.inc()
    
    session_id: Optional[str] = None
    nats_sub = None

    try:
        # ==================================================================
        # PHASE 1: HANDSHAKE
        # ==================================================================
        # Wait for the first message, which MUST be a JSON handshake
        try:
            data = await websocket.receive_text()
            # Fast parsing with orjson
            handshake_dict = orjson.loads(data)
            handshake = HandshakePayload(**handshake_dict)
            
            # TODO: Validate handshake.token (JWT) using app.core.security
            
            # Generate Session ID (In prod, use UUID or extract from JWT)
            session_id = f"session_{handshake.client_version}"
            
            # Send Acknowledgment
            ack = HandshakeAckPayload(session_id=session_id)
            await websocket.send_text(ack.model_dump_json())
            
            logger.info(f"Session established: {session_id}")
            
        except Exception as e:
            logger.error(f"Handshake failed: {e}")
            await websocket.close(code=1008) # Policy Violation
            return

        # ==================================================================
        # PHASE 2: REVERSE CHANNEL (Backend -> Client)
        # ==================================================================
        # Subscribe to 'ui.commands.{session_id}' to receive triggers from Speech Service
        
        async def ui_command_handler(msg):
            """Callback for NATS messages destined for this client."""
            try:
                # Payload is already JSON bytes from the Speech Service
                # We forward it directly to the WebSocket
                await websocket.send_text(msg.data.decode())
            except Exception as e:
                logger.error(f"[{session_id}] Error forwarding UI command: {e}")

        # Subscribe dynamically using the session_id
        if bus.nc and bus.nc.is_connected:
            nats_sub = await bus.nc.subscribe(
                f"ui.commands.{session_id}", 
                cb=ui_command_handler
            )
            logger.debug(f"[{session_id}] Subscribed to NATS return channel")
        else:
            logger.warning("NATS not connected! AI Triggers will not work.")

        # ==================================================================
        # PHASE 3: STREAMING LOOP (Client -> Backend)
        # ==================================================================
        while True:
            # Await next frame from Client
            message = await websocket.receive()

            if "bytes" in message and message["bytes"]:
                # --- AUDIO FRAME ---
                audio_chunk = message["bytes"]
                
                # Push to NATS Topic: audio.raw.{session_id}
                # This is "Fire and Forget" for speed
                await bus.publish(f"audio.raw.{session_id}", audio_chunk)

            elif "text" in message and message["text"]:
                # --- CONTROL FRAME ---
                # Handle heartbeats, mute toggle, or session end
                try:
                    payload = orjson.loads(message["text"])
                    if payload.get("type") == EventType.HEARTBEAT:
                        pass # Keep-alive logic if needed
                except orjson.JSONDecodeError:
                    pass

    except WebSocketDisconnect:
        logger.info(f"[{session_id}] Client disconnected")
        
    except Exception as e:
        logger.error(f"[{session_id}] Connection Error: {e}")
        try:
            await websocket.close(code=1011) # Internal Error
        except:
            pass
            
    finally:
        # ==================================================================
        # CLEANUP
        # ==================================================================
        ACTIVE_CONNECTIONS.dec()
        
        # Unsubscribe from NATS to stop receiving events for this dead session
        if nats_sub:
            try:
                await nats_sub.unsubscribe()
                logger.debug(f"[{session_id}] Unsubscribed from NATS")
            except Exception as e:
                logger.warning(f"Error unsubscribing: {e}")
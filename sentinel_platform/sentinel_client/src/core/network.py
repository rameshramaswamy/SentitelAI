# sentinel_client/src/core/network.py
from PyQt6.QtCore import QThread, pyqtSignal
import asyncio
import websockets
import json
from sentinel_shared.schemas.events import (
    HandshakePayload, AudioConfig, OverlayTriggerPayload, EventType
)
from sentinel_shared.utils.logger import setup_logger
import ssl

logger = setup_logger("client.network")

class NetworkWorker(QThread):
    # Signals to communicate back to Main UI Thread
    sig_connected = pyqtSignal(str) # session_id
    sig_trigger = pyqtSignal(object) # OverlayTriggerPayload
    sig_error = pyqtSignal(str)

    def __init__(self, audio_engine, gateway_url="ws://127.0.0.1:8000/ws/stream"):
        super().__init__()
        self.audio_engine = audio_engine
        self.gateway_url = gateway_url
        self.running = True

    def run(self):
        """Entry point for QThread."""
        asyncio.run(self._async_run())

    async def _async_run(self):
        retry_delay = 1
        max_delay = 30
        
        while self.running:
            logger.info(f"Connecting to {self.gateway_url}...")
            try:
                ssl_context = ssl.create_default_context()
                # OPTIMIZATION: Allow self-signed certs for localhost dev
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                async with websockets.connect(self.gateway_url, ssl=ssl_context) as ws:
                    logger.info("Socket Connected.")
                    retry_delay = 1 # Reset on success
                    
                    # 1. Handshake
                    handshake = HandshakePayload(
                        token="phase1-demo-token",
                        client_version="0.1.0",
                        audio_config=AudioConfig()
                    )
                    await ws.send(handshake.model_dump_json())
                    
                    # Wait for ACK
                    ack_raw = await ws.recv()
                    ack_data = json.loads(ack_raw)
                    
                    if ack_data.get("type") == "handshake_ack":
                        self.sig_connected.emit(ack_data.get("session_id"))
                    else:
                        logger.error("Handshake rejected")
                        await asyncio.sleep(5)
                        continue

                    # 2. Start Loops
                    send_task = asyncio.create_task(self._send_loop(ws))
                    recv_task = asyncio.create_task(self._recv_loop(ws))
                    
                    # Wait until connection drops
                    done, pending = await asyncio.wait(
                        [send_task, recv_task],
                        return_when=asyncio.FIRST_COMPLETED
                    )
                    
                    for task in pending:
                        task.cancel()

            except (websockets.exceptions.ConnectionClosed, ConnectionRefusedError) as e:
                logger.warning(f"Connection lost: {e}. Retrying in {retry_delay}s...")
                self.sig_error.emit(f"Reconnecting in {retry_delay}s...")
                
                await asyncio.sleep(retry_delay)
                # OPTIMIZATION: Exponential Backoff (1s, 2s, 4s, 8s...)
                retry_delay = min(retry_delay * 2, max_delay)
            
            except Exception as e:
                logger.error(f"Critical Network Error: {e}")
                await asyncio.sleep(5)

    async def _send_loop(self, ws):
        """Drains audio queue and sends binary frames."""
        while self.running:
            chunk = self.audio_engine.get_chunk()
            if chunk:
                await ws.send(chunk)
            else:
                await asyncio.sleep(0.01) # Small sleep to prevent CPU burn

    async def _recv_loop(self, ws):
        """Listens for AI triggers from Server."""
        while self.running:
            try:
                msg = await ws.recv()
                # Parse JSON
                data = json.loads(msg)
                
                if data.get("type") == EventType.OVERLAY_TRIGGER:
                    # Convert to Pydantic and emit to UI
                    payload = OverlayTriggerPayload(**data)
                    self.sig_trigger.emit(payload)
                    
            except websockets.exceptions.ConnectionClosed:
                break
            except Exception as e:
                logger.error(f"Receive error: {e}")
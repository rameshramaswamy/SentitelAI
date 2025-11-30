# sentinel_shared/src/schemas/events.py
from enum import Enum
from typing import Optional, Any, Dict
from uuid import UUID, uuid4
from datetime import datetime
from pydantic import BaseModel, Field

class EventType(str, Enum):
    # Client -> Server
    HANDSHAKE = "handshake"
    HEARTBEAT = "heartbeat"
    AUDIO_CONFIG = "audio_config"
    
    # Server -> Client
    HANDSHAKE_ACK = "handshake_ack"
    ERROR = "error"
    OVERLAY_TRIGGER = "overlay_trigger"

class BaseMessage(BaseModel):
    """Base envelope for all WebSocket control messages."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    type: EventType

# --- payloads ---

class AudioConfig(BaseModel):
    """Negotiates audio format. Default: 16kHz, Mono, PCM Int16"""
    sample_rate: int = 16000
    channels: int = 1
    encoding: str = "pcm_s16le" # or 'opus'
    chunk_size: int = 4096

class HandshakePayload(BaseMessage):
    """First message sent by client to authenticate."""
    type: EventType = EventType.HANDSHAKE
    token: str # JWT
    client_version: str
    audio_config: AudioConfig

class HandshakeAckPayload(BaseMessage):
    """Server response to handshake."""
    type: EventType = EventType.HANDSHAKE_ACK
    session_id: str
    reconnect_token: Optional[str] = None

class OverlayContent(BaseModel):
    """Data to be rendered on the Desktop UI."""
    title: str
    message: str
    action_items: list[str] = []
    sentiment: Optional[str] = "neutral"
    color_hex: str = "#FFFFFF"

class OverlayTriggerPayload(BaseMessage):
    """Instruction for Client to show UI."""
    type: EventType = EventType.OVERLAY_TRIGGER
    content: OverlayContent
    display_duration_ms: int = 5000
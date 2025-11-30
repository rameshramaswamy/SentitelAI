import pytest
from sentinel_shared.schemas.events import (
    HandshakePayload, AudioConfig, EventType, OverlayTriggerPayload
)

def test_handshake_serialization():
    """Ensure handshake model serializes/deserializes correctly."""
    payload = HandshakePayload(
        token="fake-jwt",
        client_version="1.0.0",
        audio_config=AudioConfig(sample_rate=44100)
    )
    
    json_output = payload.model_dump_json()
    assert "fake-jwt" in json_output
    assert payload.type == EventType.HANDSHAKE

def test_overlay_trigger_structure():
    """Ensure UI triggers define required fields."""
    trigger = OverlayTriggerPayload(
        content={
            "title": "Objection", 
            "message": "Too expensive",
            "color_hex": "#FF0000"
        }
    )
    assert trigger.content.title == "Objection"
    assert trigger.type == EventType.OVERLAY_TRIGGER
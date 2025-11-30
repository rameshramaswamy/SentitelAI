import pytest
import numpy as np
from src.core.audio_buffer import AudioBuffer
from src.core.nlp_router import NLPRouter

# Note: We skip VAD/Transcriber in unit tests unless we mock the heavy models,
# as loading them takes time. Here we test Buffer and Logic.

def test_audio_buffer_conversion():
    buf = AudioBuffer()
    # Create fake Int16 silence (zeros)
    fake_pcm = bytes([0] * 32000) # ~1 second at 16khz (2 bytes per sample)
    
    buf.add_bytes(fake_pcm)
    
    assert buf.get_duration() == 1.0
    audio_out = buf.get_audio()
    assert audio_out.dtype == np.float32
    assert len(audio_out) == 16000

def test_nlp_router_match():
    router = NLPRouter()
    
    # Positive Match
    result = router.process("I am worried about the budget of this project.")
    assert result is not None
    assert result["title"] == "Pricing Objection"
    
    # Negative Match
    result = router.process("Hello world.")
    assert result is None
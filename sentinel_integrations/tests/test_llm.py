# sentinel_integrations/tests/test_llm.py
import pytest
import json
from src.llm.prompts import PromptManager
from src.llm.engine import LLMEngine
from src.config import settings

# Force Mock Mode for tests
settings.LLM_MOCK_MODE = True

def test_prompt_rendering():
    pm = PromptManager()
    transcript = "Hello, I want to buy your product."
    rendered = pm.render_summary_prompt(transcript)
    
    assert "TRANSCRIPT:" in rendered
    assert "Hello, I want to buy your product." in rendered

@pytest.mark.asyncio
async def test_engine_mock_response():
    engine = LLMEngine()
    transcript = "This is a long conversation about sales..."
    
    result = await engine.generate_summary(transcript)
    
    assert "summary" in result
    assert "action_items" in result
    assert isinstance(result["action_items"], list)
    assert result["sentiment"] in ["Positive", "Neutral", "Negative"]
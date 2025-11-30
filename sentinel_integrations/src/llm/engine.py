# sentinel_integrations/src/llm/engine.py
import json
import logging
import asyncio
from openai import AsyncOpenAI
from src.config import settings
from src.llm.prompts import PromptManager

logger = logging.getLogger("llm.engine")

class LLMEngine:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.prompts = PromptManager()

    async def generate_summary(self, transcript: str) -> dict:
        """
        Sends transcript to LLM and returns structured JSON.
        """
        if not transcript or len(transcript) < 50:
            logger.warning("Transcript too short for summary.")
            return {}

        # 1. Mock Mode (Dev / Cost Savings)
        if settings.LLM_MOCK_MODE:
            logger.info("Mock Mode: Returning synthetic summary.")
            await asyncio.sleep(1) # Simulate network latency
            return {
                "summary": "The customer was interested in the Enterprise plan but had concerns about the timeline.",
                "action_items": ["Send technical specs", "Schedule follow-up with CTO"],
                "sentiment": "Neutral",
                "objections": ["Timeline"],
                "deal_risk_score": 4
            }

        # 2. Render Prompt
        prompt_text = self.prompts.render_summary_prompt(transcript)

        try:
            # 3. Call API
            response = await self.client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[
                    {"role": "system", "content": "You are a helpful AI assistant that outputs JSON."},
                    {"role": "user", "content": prompt_text}
                ],
                response_format={"type": "json_object"},
                temperature=0.3, # Low temperature for factual extraction
            )
            
            content = response.choices[0].message.content
            
            # 4. Parse JSON
            return json.loads(content)

        except Exception as e:
            logger.error(f"LLM Generation Failed: {e}")
            return {"error": str(e)}
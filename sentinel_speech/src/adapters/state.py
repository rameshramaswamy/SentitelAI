# Redis Client Wrapper# sentinel_speech/src/adapters/state.py
import redis.asyncio as redis
from src.core.config import settings

class StateManager:
    def __init__(self):
        # We assume localhost for Phase 2 dev, typically passed via Env in Prod
        redis_url = "redis://localhost:6379" 
        self.redis = redis.from_url(redis_url, encoding="utf-8", decode_responses=True)

    async def append_transcript(self, session_id: str, text: str):
        """Appends new text to the session's running transcript."""
        key = f"transcript:{session_id}"
        # Append text with a space
        await self.redis.append(key, f" {text}")
        # Set expiry (1 day) to clean up old keys
        await self.redis.expire(key, 86400)

    async def close(self):
        await self.redis.close()
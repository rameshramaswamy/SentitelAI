# sentinel_gateway/app/adapters/nats_adapter.py
import nats
from nats.aio.client import Client as NATS
from app.core.config import settings
from app.utils.logger import logger
from .bus_interface import BusAdapter

class NatsAdapter(BusAdapter):
    def __init__(self):
        self.nc = NATS()

    async def connect(self):
        try:
            await self.nc.connect(settings.NATS_URL)
            logger.info(f"Connected to NATS at {settings.NATS_URL}")
        except Exception as e:
            logger.error(f"Failed to connect to NATS: {e}")
            raise e

    async def publish(self, subject: str, payload: bytes):
        if self.nc.is_connected:
            await self.nc.publish(subject, payload)
        else:
            logger.warning("NATS not connected, dropping message")

    async def close(self):
        await self.nc.close()
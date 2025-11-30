# sentinel_gateway/app/adapters/bus_interface.py
from abc import ABC, abstractmethod
from typing import Any

class BusAdapter(ABC):
    @abstractmethod
    async def connect(self):
        """Establish connection to the broker."""
        pass

    @abstractmethod
    async def publish(self, subject: str, payload: bytes):
        """Fire and forget message."""
        pass

    @abstractmethod
    async def close(self):
        """Graceful shutdown."""
        pass
# sentinel_integrations/src/crm/base.py
from abc import ABC, abstractmethod
from typing import Dict, Optional

class BaseCRM(ABC):
    @abstractmethod
    async def connect(self):
        """Authenticate with the CRM."""
        pass

    @abstractmethod
    async def log_call_activity(self, 
                                user_email: str, 
                                customer_email: str, 
                                summary_data: Dict) -> bool:
        """
        Logs the summary, action items, and sentiment to the CRM.
        Returns True if successful.
        """
        pass
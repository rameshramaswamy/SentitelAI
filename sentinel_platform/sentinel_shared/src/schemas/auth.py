# sentinel_shared/src/schemas/auth.py
from pydantic import BaseModel
from typing import List, Optional

class UserRole(str):
    ADMIN = "admin"
    AGENT = "agent"

class TenantContext(BaseModel):
    """Extracted from JWT, passed internally to services."""
    user_id: str
    org_id: str
    roles: List[str]
    tier: str = "standard"
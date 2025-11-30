# sentinel_security/src/models/audit_log.py
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import uuid4, UUID
from typing import Optional, Dict, Any

class AuditEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # WHO
    actor_id: str  # User UUID or System Service Name
    tenant_id: Optional[str] = None
    ip_address: Optional[str] = "0.0.0.0"
    
    # WHAT
    action: str  # e.g., "LOGIN", "VIEW_TRANSCRIPT", "GENERATE_HINT"
    resource_id: Optional[str] = None # e.g., call_id
    
    # OUTCOME
    status: str = "SUCCESS" # SUCCESS, FAILURE, DENIED
    metadata: Dict[str, Any] = {}
    
    # INTEGRITY (Populated by the Consumer, not the Producer)
    prev_hash: Optional[str] = None
    signature: Optional[str] = None
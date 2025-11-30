# sentinel_security/src/workers/audit_consumer.py
import asyncio
import json
import hashlib
import logging
import os
import aiofiles
from datetime import datetime
import nats
from src.config import settings
from src.models.audit_log import AuditEvent

logger = logging.getLogger("worker.audit")

class AuditConsumer:
    def __init__(self):
        self.nc = None
        self.log_file = "audit_trail.jsonl"
        self.last_hash = self._get_last_hash()

    def _get_last_hash(self) -> str:
        """Reads the last line of the log file to get the previous hash."""
        if not os.path.exists(self.log_file):
            return "0" * 64 # Genesis Hash
        
        try:
            # Read last line efficiently (in prod use a pointer)
            with open(self.log_file, 'rb') as f:
                try:
                    f.seek(-2, os.SEEK_END)
                    while f.read(1) != b'\n':
                        f.seek(-2, os.SEEK_CUR)
                except OSError:
                    f.seek(0)
                last_line = f.readline().decode()
                
            if not last_line:
                return "0" * 64
                
            data = json.loads(last_line)
            # Re-calculate hash of the last record to verify integrity
            return self._calculate_hash(data)
        except Exception:
            return "0" * 64

    def _calculate_hash(self, event_dict: dict) -> str:
        """Creates a SHA-256 fingerprint of the event."""
        # Ensure deterministic ordering of keys
        serialized = json.dumps(event_dict, sort_keys=True).encode()
        return hashlib.sha256(serialized).hexdigest()

    async def start(self):
        self.nc = await nats.connect(settings.NATS_URL if hasattr(settings, 'NATS_URL') else "nats://localhost:4222")
        logger.info("Audit Consumer Connected to NATS.")

        # Subscribe to all audit events
        await self.nc.subscribe("audit.>", cb=self.handle_event)
        
        # Keep alive
        while True:
            await asyncio.sleep(1)

    async def handle_event(self, msg):
        try:
            payload = json.loads(msg.data.decode())
            
            # 1. Validate Schema
            event = AuditEvent(**payload)
            
            # 2. Cryptographic Chaining
            event.prev_hash = self.last_hash
            
            # 3. Serialize
            event_dict = event.model_dump(mode='json')
            
            # 4. Calculate New Hash (for next link)
            current_hash = self._calculate_hash(event_dict)
            self.last_hash = current_hash
            
            # 5. Append to Immutable Log (Local File for Phase 4)
            async with aiofiles.open(self.log_file, "a") as f:
                await f.write(json.dumps(event_dict) + "\n")
                
            logger.info(f"Audited: {event.action} by {event.actor_id}")

        except Exception as e:
            logger.error(f"Audit processing failed: {e}")
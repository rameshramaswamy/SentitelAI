# sentinel_security/src/main.py
import asyncio
import logging
from src.workers.audit_consumer import AuditConsumer
from sentinel_shared.utils.logger import setup_logger

logger = setup_logger("audit_service", "INFO")

if __name__ == "__main__":
    consumer = AuditConsumer()
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        logger.info("Starting Sentinel Audit Service (Compliance)...")
        loop.run_until_complete(consumer.start())
    except KeyboardInterrupt:
        logger.info("Stopping...")
    finally:
        loop.close()
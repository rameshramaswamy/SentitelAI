# sentinel_integrations/src/main.py
import asyncio
import logging
from src.workers.post_call_worker import PostCallWorker
from sentinel_shared.utils.logger import setup_logger

logger = setup_logger("integration_service", "INFO")

if __name__ == "__main__":
    worker = PostCallWorker()
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        logger.info("Starting Sentinel Integration Service...")
        loop.run_until_complete(worker.start())
    except KeyboardInterrupt:
        logger.info("Stopping...")
    finally:
        loop.close()
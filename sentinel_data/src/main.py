# sentinel_data/src/main.py
import signal
import asyncio
import logging
from src.workers.persistence_worker import PersistenceWorker
from sentinel_shared.utils.logger import setup_logger

logger = setup_logger("data_service", "INFO")

async def shutdown_handler(worker, loop):
    logger.warning("Received SIGTERM. Flushing buffers...")
    
    # 1. Flush DB Queue
    await worker.flush_db()
    
    # 2. Finalize all active audio sessions (Upload what we have)
    # (Assuming worker exposes a list of active_session_ids)
    tasks = [worker.finalize_session(sid) for sid in worker.active_files.keys()]
    if tasks:
        await asyncio.gather(*tasks)
        
    logger.info("Graceful shutdown complete.")
    loop.stop()

if __name__ == "__main__":
    worker = PersistenceWorker()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # OPTIMIZATION: Register Signal Handlers
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(
            sig, 
            lambda: asyncio.create_task(shutdown_handler(worker, loop))
        )

    try:
        loop.run_until_complete(worker.start())
    except Exception as e:
        pass # loop handled in shutdown
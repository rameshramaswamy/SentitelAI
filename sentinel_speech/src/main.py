# Service Entrypoint# sentinel_speech/src/main.py
import asyncio
import logging
from src.workers.stream_processor import StreamProcessor
from sentinel_shared.utils.logger import setup_logger

# Setup structured logging
logger = setup_logger("speech_service", "INFO")

if __name__ == "__main__":
    processor = StreamProcessor()
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        logger.info("Starting Sentinel Speech Worker...")
        loop.run_until_complete(processor.start())
    except KeyboardInterrupt:
        logger.info("Stopping...")
        loop.run_until_complete(processor.shutdown())
    finally:
        loop.close()
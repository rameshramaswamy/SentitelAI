# sentinel_shared/src/utils/logger.py
import logging
import sys
from pythonjsonlogger import jsonlogger

def setup_logger(name: str, level: str = "INFO"):
    """
    Returns a logger configured for JSON output.
    """
    logger = logging.getLogger(name)
    
    # Prevent duplicate handlers if function called multiple times
    if logger.hasHandlers():
        return logger
        
    logger.setLevel(level)
    
    handler = logging.StreamHandler(sys.stdout)
    
    # Format: {"timestamp": "...", "level": "INFO", "message": "...", "module": "..."}
    formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(levelname)s %(name)s %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger
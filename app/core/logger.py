import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logging():
    log_dir = "data"
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "files.log")

    # Rotate with max 100kb, keep up to 3 backups
    handler = RotatingFileHandler(
        log_file,
        maxBytes=100 * 1024,
        backupCount=3
    )

    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s"
    )
    handler.setFormatter(formatter)

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Remove any existing handlers to avoid duplicates during reload
    if root_logger.hasHandlers():
        root_logger.handlers.clear()
        
    root_logger.addHandler(handler)

    # Optionally add to console output
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

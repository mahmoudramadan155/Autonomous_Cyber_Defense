import asyncio
import logging
import sys
from app.workers import process_logs_raw_stream, process_alerts_stream, process_incidents_stream
from app.core.logger import setup_logging
from app.db.session import init_db

setup_logging()
logger = logging.getLogger(__name__)

async def main(worker_type: str):
    logger.info("Initializing worker database connection...")
    await init_db()
    
    if worker_type == "detection":
        logger.info("Starting Threat & Anomaly Detection Worker...")
        await process_logs_raw_stream()
    elif worker_type == "correlation":
        logger.info("Starting Correlation Worker...")
        await process_alerts_stream()
    elif worker_type == "response":
        logger.info("Starting Risk & Response Worker...")
        await process_incidents_stream()
    else:
        logger.error(f"Unknown worker type: {worker_type}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m app.worker_main <detection|correlation|response>")
        sys.exit(1)
        
    worker_type = sys.argv[1]
    
    try:
        asyncio.run(main(worker_type))
    except KeyboardInterrupt:
        logger.info("Worker stopped.")

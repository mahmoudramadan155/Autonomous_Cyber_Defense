from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.session import get_db
from app.schemas.log import LogEventCreate, LogEvent
from app.services.log_collector import LogCollectorService
from app.services.threat_detection import ThreatDetectionService
from app.services.anomaly_detection import AnomalyDetectionService
from app.services.correlation_engine import CorrelationEngine
import logging

router = APIRouter()

anomaly_service = AnomalyDetectionService()

async def process_log_background(log_in: LogEventCreate):
    from app.db.session import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        collector = LogCollectorService(db)
        await collector.collect_log(log_in)

async def process_bulk_logs_background(logs_in: List[LogEventCreate]):
    from app.db.session import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        collector = LogCollectorService(db)
        await collector.bulk_collect_logs(logs_in)


@router.post("/logs", response_model=dict, status_code=202)
async def ingest_log(log_in: LogEventCreate, background_tasks: BackgroundTasks):
    """
    Ingests a single log event and processes it asynchronously.
    """
    logging.info(f"Received single log ingestion request from source: {log_in.source}")
    background_tasks.add_task(process_log_background, log_in)
    return {"status": "Processing initiated"}

@router.post("/logs/bulk", response_model=dict, status_code=202)
async def ingest_logs_bulk(logs_in: List[LogEventCreate], background_tasks: BackgroundTasks):
    """
    Ingests multiple log events.
    """
    logging.info(f"Received bulk log ingestion request: {len(logs_in)} logs")
    background_tasks.add_task(process_bulk_logs_background, logs_in)
    return {"status": f"Processing {len(logs_in)} logs initiated"}

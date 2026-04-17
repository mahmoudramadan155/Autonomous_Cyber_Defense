import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.db.session import init_db
from app.api import api_router
from app.core.config import settings
from app.core.logger import setup_logging


import asyncio
from app.workers import process_logs_raw_stream, process_alerts_stream, process_incidents_stream

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize the database and logger on startup."""
    setup_logging()
    logging.info("Initializing Autonomous Cyber Defense Platform...")
    await init_db()
    logging.info("Database synchronized and models loaded successfully.")
    
    yield
    
    logging.info("Shutting down platform.")

app = FastAPI(
    title=settings.app_name,
    description="Autonomous Cyber Defense & Threat Intelligence Platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/", tags=["Health"])
async def root():
    # Triggered reload to recreate db
    return {"status": "ok", "platform": settings.app_name}

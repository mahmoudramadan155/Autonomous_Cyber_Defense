from fastapi import APIRouter
from app.api.routes import ingest, alerts, incidents, response, simulate, dashboard
from app.api.routes import blocked_ips, cases, search, websocket

api_router = APIRouter()

api_router.include_router(ingest.router,      prefix="/ingest",       tags=["Log Ingestion"])
api_router.include_router(alerts.router,      prefix="/alerts",       tags=["Alerts"])
api_router.include_router(incidents.router,   prefix="/incidents",    tags=["Incidents"])
api_router.include_router(response.router,    prefix="/response",     tags=["Response Engine"])
api_router.include_router(simulate.router,    prefix="/red-team",     tags=["Attack Simulation"])
api_router.include_router(dashboard.router,   prefix="/dashboard",    tags=["Dashboard"])
api_router.include_router(blocked_ips.router, prefix="/blocked-ips",  tags=["Blocked IPs"])
api_router.include_router(cases.router,       prefix="/cases",        tags=["Case Management"])
api_router.include_router(search.router,      prefix="/search",       tags=["Search"])
api_router.include_router(websocket.router,   prefix="/ws",           tags=["WebSocket"])

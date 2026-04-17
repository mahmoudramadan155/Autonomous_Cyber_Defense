"""
WebSocket endpoint for real-time alert/incident broadcasting.
All detection services notify this hub which broadcasts to connected clients.
"""
import asyncio
import json
import logging
from typing import Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)
router = APIRouter()

# Global set of connected WebSocket clients
_clients: Set[WebSocket] = set()


async def broadcast(message: dict):
    """Broadcast a message to all connected WebSocket clients."""
    if not _clients:
        return
    dead = set()
    text = json.dumps(message, default=str)
    for ws in _clients.copy():
        try:
            await ws.send_text(text)
        except Exception:
            dead.add(ws)
    _clients -= dead


@router.websocket("/alerts")
async def ws_alerts(websocket: WebSocket):
    """Real-time alert stream WebSocket endpoint."""
    await websocket.accept()
    _clients.add(websocket)
    logger.info(f"WebSocket client connected. Total: {len(_clients)}")
    try:
        while True:
            # Keep the connection alive; client can also send pings
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30)
            except asyncio.TimeoutError:
                # Send a heartbeat
                await websocket.send_text(json.dumps({"type": "heartbeat"}))
    except WebSocketDisconnect:
        pass
    finally:
        _clients.discard(websocket)
        logger.info(f"WebSocket client disconnected. Total: {len(_clients)}")

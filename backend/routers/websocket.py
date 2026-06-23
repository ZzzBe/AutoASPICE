"""
WebSocket router for real-time agent output streaming.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import logging

from shared.state import get_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/{project_id}/{node_id}")
async def agent_websocket(ws: WebSocket, project_id: str, node_id: str):
    """WebSocket endpoint for real-time agent execution output."""
    output_stream = get_service("output_stream")
    if output_stream is None:
        await ws.accept()
        await ws.send_text(json.dumps({
            "type": "error",
            "message": "Output stream not initialized",
        }))
        await ws.close()
        return

    await ws.accept()
    await output_stream.subscribe(node_id, ws)

    # Send connection confirmation
    await ws.send_text(json.dumps({
        "type": "connection",
        "status": "connected",
        "project_id": project_id,
        "node_id": node_id,
    }))

    try:
        # Keep connection alive - listen for messages from client
        while True:
            data = await ws.receive_text()
            try:
                msg = json.loads(data)
                action = msg.get("action", "")
                if action == "ping":
                    await ws.send_text(json.dumps({"type": "pong"}))
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        logger.info(f"[ws] Client disconnected: {project_id}/{node_id}")
    except Exception as e:
        logger.error(f"[ws] Error: {project_id}/{node_id}: {e}")
    finally:
        await output_stream.unsubscribe(node_id, ws)

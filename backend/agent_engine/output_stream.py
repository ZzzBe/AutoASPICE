import asyncio
import json
from typing import Dict, List, Optional
from shared.models import AgentMessage


class OutputStreamManager:
    """
    Buffers agent execution output and dispatches messages to WebSocket connections.
    Maintains per-node output buffers and manages subscriber connections.
    """

    def __init__(self):
        # node_id -> list of WebSocket connections
        self._subscribers: Dict[str, List] = {}
        # node_id -> list of buffered messages
        self._buffers: Dict[str, List[AgentMessage]] = {}
        # node_id -> bool (whether execution is active)
        self._active: Dict[str, bool] = {}
        self._lock = asyncio.Lock()

    async def subscribe(self, node_id: str, websocket) -> None:
        """Subscribe a WebSocket connection to a node's output stream."""
        async with self._lock:
            if node_id not in self._subscribers:
                self._subscribers[node_id] = []
            self._subscribers[node_id].append(websocket)

            # Replay buffered messages to the new subscriber
            if node_id in self._buffers:
                for msg in self._buffers[node_id]:
                    try:
                        await websocket.send_json(msg.model_dump())
                    except Exception:
                        pass

    async def unsubscribe(self, node_id: str, websocket) -> None:
        """Unsubscribe a WebSocket connection from a node's output stream."""
        async with self._lock:
            if node_id in self._subscribers:
                self._subscribers[node_id] = [
                    ws for ws in self._subscribers[node_id] if ws != websocket
                ]
                if not self._subscribers[node_id]:
                    del self._subscribers[node_id]

    async def push(self, node_id: str, msg_type: str, data: dict = None) -> None:
        """Push a message to all subscribers of a node."""
        message = AgentMessage(
            type=msg_type,
            node_id=node_id,
            data=data or {},
        )
        await self._broadcast(node_id, message)

    async def _broadcast(self, node_id: str, message: AgentMessage) -> None:
        """Send a message to all connected subscribers and buffer it."""
        async with self._lock:
            # Buffer the message
            if node_id not in self._buffers:
                self._buffers[node_id] = []
            self._buffers[node_id].append(message)

            # Trim buffer to last 500 messages to avoid memory bloat
            if len(self._buffers[node_id]) > 500:
                self._buffers[node_id] = self._buffers[node_id][-500:]

            # Send to subscribers
            if node_id in self._subscribers:
                dead_sockets = []
                for ws in self._subscribers[node_id]:
                    try:
                        await ws.send_json(message.model_dump())
                    except Exception:
                        dead_sockets.append(ws)
                for ws in dead_sockets:
                    self._subscribers[node_id].remove(ws)

    async def set_active(self, node_id: str, active: bool) -> None:
        """Mark a node's execution as active or inactive."""
        async with self._lock:
            self._active[node_id] = active
            if not active and node_id in self._buffers:
                # Optionally flush buffers when execution is done
                pass

    def is_active(self, node_id: str) -> bool:
        return self._active.get(node_id, False)

    async def clear_buffer(self, node_id: str) -> None:
        """Clear the output buffer for a node."""
        async with self._lock:
            if node_id in self._buffers:
                del self._buffers[node_id]

    def get_buffer(self, node_id: str) -> List[AgentMessage]:
        """Get the current buffer for a node (for status queries)."""
        return list(self._buffers.get(node_id, []))

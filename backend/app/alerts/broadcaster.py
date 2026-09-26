"""Real-time event broadcaster supporting WebSockets and Server-Sent Events (SSE)."""

import asyncio
import json
import logging
from typing import Any, AsyncGenerator, Dict, List, Set
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class AlertBroadcaster:
    """Manages active WebSockets and SSE subscriber queues for real-time dashboard updates."""

    def __init__(self):
        self._active_websockets: Set[WebSocket] = set()
        self._sse_queues: Set[asyncio.Queue] = set()
        self._lock = asyncio.Lock()

    # --- WebSocket Management ---

    async def connect_ws(self, websocket: WebSocket) -> None:
        """Register newly connected WebSocket client."""
        await websocket.accept()
        async with self._lock:
            self._active_websockets.add(websocket)
        logger.info(f"WebSocket client connected. Active subscribers: {len(self._active_websockets)}")

    async def disconnect_ws(self, websocket: WebSocket) -> None:
        """Deregister disconnected WebSocket client."""
        async with self._lock:
            self._active_websockets.discard(websocket)
        logger.info(f"WebSocket client disconnected. Active subscribers: {len(self._active_websockets)}")

    # --- Server-Sent Events (SSE) Management ---

    async def subscribe_sse(self) -> AsyncGenerator[str, None]:
        """Subscribe an SSE client and yield event stream strings."""
        queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        async with self._lock:
            self._sse_queues.add(queue)

        try:
            # Yield initial connection confirmation
            init_event = json.dumps({"type": "CONNECTED", "message": "Subscribed to Golden-Hour alert feed"})
            yield f"data: {init_event}\n\n"

            while True:
                msg = await queue.get()
                yield f"data: {json.dumps(msg)}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            async with self._lock:
                self._sse_queues.discard(queue)

    # --- Broadcast Dispatcher ---

    async def broadcast(self, payload: Dict[str, Any]) -> None:
        """Broadcast an alert event to all connected WebSockets and SSE clients."""
        msg_str = json.dumps(payload)

        # 1. Dispatch WebSockets
        dead_ws = set()
        async with self._lock:
            ws_targets = list(self._active_websockets)

        for ws in ws_targets:
            try:
                await ws.send_text(msg_str)
            except Exception as e:
                logger.warning(f"Error sending to WebSocket client: {e}")
                dead_ws.add(ws)

        if dead_ws:
            async with self._lock:
                for ws in dead_ws:
                    self._active_websockets.discard(ws)

        # 2. Dispatch SSE Queues
        async with self._lock:
            sse_targets = list(self._sse_queues)

        for q in sse_targets:
            try:
                q.put_nowait(payload)
            except asyncio.QueueFull:
                logger.warning("SSE queue full; dropping message for subscriber")
            except Exception:
                pass


# Global singleton instance
alert_broadcaster = AlertBroadcaster()

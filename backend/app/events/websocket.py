import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.auth.service import verify_token
from app.events.service import get_latest_events

router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass


manager = ConnectionManager()


async def broadcast_new_event(event: dict):
    """Call this function when a new event is detected to broadcast to all connected clients."""
    await manager.broadcast({"type": "event", "data": event})


async def broadcast_device_update(device: dict):
    """Broadcast updated device metrics whenever a heartbeat is processed."""
    await manager.broadcast({"type": "device_update", "data": device})


@router.websocket("/ws/events")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
):
    # Verify token
    token_data = verify_token(token, token_type="access")
    if token_data is None:
        await websocket.close(code=4001, reason="Unauthorized")
        return

    await manager.connect(websocket)

    try:
        # Send initial batch of recent events
        recent_events = get_latest_events(limit=10)
        await websocket.send_json({
            "type": "initial",
            "data": [event.model_dump(mode="json") for event in recent_events],
        })

        # Keep connection alive and handle messages
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                message = json.loads(data)

                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                elif message.get("type") == "subscribe":
                    # Could implement topic-based subscriptions here
                    await websocket.send_json({"type": "subscribed", "topic": message.get("topic")})
                elif message.get("type") == "unsubscribe":
                    await websocket.send_json({"type": "unsubscribed", "topic": message.get("topic")})

            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                try:
                    await websocket.send_json({"type": "ping"})
                except Exception:
                    break

    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        manager.disconnect(websocket)

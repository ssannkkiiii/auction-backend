import json
from collections import defaultdict

from fastapi import WebSocket


class LotConnectionManager:
    """Зберігає WebSocket-підключення по lot_id та розсилає повідомлення."""

    def __init__(self) -> None:
        self._connections: dict[int, list[WebSocket]] = defaultdict(list)

    async def connect(self, websocket: WebSocket, lot_id: int) -> None:
        await websocket.accept()
        self._connections[lot_id].append(websocket)

    def disconnect(self, websocket: WebSocket, lot_id: int) -> None:
        if lot_id in self._connections:
            try:
                self._connections[lot_id].remove(websocket)
            except ValueError:
                pass
            if not self._connections[lot_id]:
                del self._connections[lot_id]

    async def broadcast_to_lot(self, lot_id: int, message: dict) -> None:
        if lot_id not in self._connections:
            return
        dead: list[WebSocket] = []
        payload = json.dumps(message)
        for ws in self._connections[lot_id]:
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws, lot_id)


ws_manager = LotConnectionManager()

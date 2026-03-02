from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select

from backend.db import Lot
from backend.db.session import async_session_factory
from backend.services.websocket_manager import ws_manager

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/lots/{lot_id}")
async def websocket_lot_events(websocket: WebSocket, lot_id: int) -> None:
    async with async_session_factory() as db:
        result = await db.execute(select(Lot).where(Lot.id == lot_id))
        lot = result.scalar_one_or_none()
        if not lot:
            await websocket.close(code=4404)
            return

    await ws_manager.connect(websocket, lot_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        ws_manager.disconnect(websocket, lot_id)

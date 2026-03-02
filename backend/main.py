from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.api import lots_router, ws_router
from backend.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="Auction API",
    description="Аукціон: лоти, ставки, оновлення в реальному часі через WebSocket",
    lifespan=lifespan,
)

app.include_router(lots_router)
app.include_router(ws_router)

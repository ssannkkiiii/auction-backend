from datetime import datetime, timezone, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.conf import settings
from backend.db import get_db, Lot, Bid, LotStatus
from backend.schemas import LotCreate, LotResponse, LotListResponse, BidCreate, BidPlacedMessage, TimeExtendedMessage
from backend.services.websocket_manager import ws_manager

router = APIRouter(prefix="/lots", tags=["lots"])


@router.post("", response_model=LotResponse)
async def create_lot(
    payload: LotCreate,
    db: AsyncSession = Depends(get_db),
) -> Lot:
    lot = Lot(
        title=payload.title,
        description=payload.description,
        start_price=payload.start_price,
        status=LotStatus.running,
    )
    db.add(lot)
    await db.flush()
    await db.refresh(lot)
    return lot


@router.get("", response_model=list[LotListResponse])
async def list_lots(
    db: AsyncSession = Depends(get_db),
) -> list[Lot]:
    result = await db.execute(
        select(Lot).where(Lot.status == LotStatus.running).order_by(Lot.created_at.desc())
    )
    return list(result.scalars().all())


@router.get("/{lot_id}", response_model=LotResponse)
async def get_lot(
    lot_id: int,
    db: AsyncSession = Depends(get_db),
) -> Lot:
    result = await db.execute(select(Lot).where(Lot.id == lot_id))
    lot = result.scalar_one_or_none()
    if not lot:
        raise HTTPException(status_code=404, detail="Lot not found")
    return lot


@router.post("/{lot_id}/bids")
async def place_bid(
    lot_id: int,
    payload: BidCreate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(select(Lot).where(Lot.id == lot_id))
    lot = result.scalar_one_or_none()
    if not lot:
        raise HTTPException(status_code=404, detail="Lot not found")
    if lot.status != LotStatus.running:
        raise HTTPException(status_code=400, detail="Lot is not accepting bids")

    last_bid_result = await db.execute(
        select(Bid).where(Bid.lot_id == lot_id).order_by(Bid.amount.desc()).limit(1)
    )
    last_bid = last_bid_result.scalar_one_or_none()
    min_amount = float(lot.start_price) if not last_bid else float(last_bid.amount)
    if payload.amount <= min_amount:
        raise HTTPException(
            status_code=400,
            detail=f"Bid must be greater than {min_amount}",
        )

    bid = Bid(lot_id=lot_id, bidder=payload.bidder, amount=payload.amount)
    db.add(bid)
    await db.flush()

    now = datetime.now(timezone.utc)
    if settings.BID_EXTEND_MINUTES > 0:
        if lot.end_time is None or lot.end_time < now:
            lot.end_time = now + timedelta(minutes=settings.BID_EXTEND_MINUTES)
        else:
            lot.end_time = lot.end_time + timedelta(minutes=settings.BID_EXTEND_MINUTES)
        await db.flush()

    msg_bid = BidPlacedMessage(lot_id=lot_id, bidder=payload.bidder, amount=payload.amount)
    await ws_manager.broadcast_to_lot(lot_id, msg_bid.model_dump())

    if lot.end_time:
        msg_time = TimeExtendedMessage(lot_id=lot_id, end_time=lot.end_time.isoformat())
        await ws_manager.broadcast_to_lot(lot_id, msg_time.model_dump())

    return {
        "id": bid.id,
        "lot_id": lot_id,
        "bidder": payload.bidder,
        "amount": float(bid.amount),
        "created_at": bid.created_at.isoformat(),
    }

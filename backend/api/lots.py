from datetime import datetime, timezone, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from backend.core.conf import settings
from backend.db import get_db, Lot, Bid, LotStatus
from backend.schemas import LotCreate, LotResponse, LotListResponse, BidCreate, BidPlacedMessage, TimeExtendedMessage
from backend.services.websocket_manager import ws_manager

router = APIRouter(prefix="/lots", tags=["lots"])


def _lot_to_response(lot: Lot, current_price: Decimal | None = None) -> LotResponse:
    price = current_price if current_price is not None else lot.start_price
    return LotResponse(
        id=lot.id,
        title=lot.title,
        description=lot.description,
        start_price=lot.start_price,
        current_price=price,
        status=lot.status,
        end_time=lot.end_time,
        created_at=lot.created_at,
    )


@router.post("", response_model=LotResponse)
async def create_lot(
    payload: LotCreate,
    db: AsyncSession = Depends(get_db),
) -> LotResponse:
    lot = Lot(
        title=payload.title,
        description=payload.description,
        start_price=payload.start_price,
        status=LotStatus.running,
    )
    db.add(lot)
    await db.flush()
    await db.refresh(lot)
    return _lot_to_response(lot)


@router.get("", response_model=list[LotListResponse])
async def list_lots(
    db: AsyncSession = Depends(get_db),
) -> list[LotListResponse]:
    result = await db.execute(
        select(Lot).where(Lot.status == LotStatus.running).order_by(Lot.created_at.desc())
    )
    lots = list(result.scalars().all())
    if not lots:
        return []
    lot_ids = [lot.id for lot in lots]
    max_bids = await db.execute(
        select(Bid.lot_id, func.max(Bid.amount).label("max_amount"))
        .where(Bid.lot_id.in_(lot_ids))
        .group_by(Bid.lot_id)
    )
    current_by_lot = {row.lot_id: row.max_amount for row in max_bids.all()}
    return [
        LotListResponse(
            id=lot.id,
            title=lot.title,
            description=lot.description,
            start_price=lot.start_price,
            current_price=current_by_lot.get(lot.id) or lot.start_price,
            status=lot.status,
            end_time=lot.end_time,
            created_at=lot.created_at,
        )
        for lot in lots
    ]


@router.get("/{lot_id}", response_model=LotResponse)
async def get_lot(
    lot_id: int,
    db: AsyncSession = Depends(get_db),
) -> LotResponse:
    result = await db.execute(select(Lot).where(Lot.id == lot_id))
    lot = result.scalar_one_or_none()
    if not lot:
        raise HTTPException(status_code=404, detail="Lot not found")
    max_bid = await db.execute(
        select(func.max(Bid.amount)).where(Bid.lot_id == lot_id)
    )
    current_price = max_bid.scalar_one_or_none() or lot.start_price
    return _lot_to_response(lot, current_price)


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

    new_price = float(payload.amount)
    msg_bid = BidPlacedMessage(
        lot_id=lot_id,
        bidder=payload.bidder,
        amount=payload.amount,
        start_price=float(lot.start_price),
        current_price=new_price,
        new_bid_display=f"{payload.bidder} поставив {new_price:.2f}",
    )
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

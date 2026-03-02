from pydantic import BaseModel


class BidCreate(BaseModel):
    bidder: str
    amount: float


class BidPlacedMessage(BaseModel):
    type: str = "bid_placed"
    lot_id: int
    bidder: str
    amount: float


class TimeExtendedMessage(BaseModel):
    type: str = "time_extended"
    lot_id: int
    end_time: str  # ISO format

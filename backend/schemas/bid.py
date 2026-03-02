from pydantic import BaseModel


class BidCreate(BaseModel):
    bidder: str
    amount: float


class BidPlacedMessage(BaseModel):
    """Повідомлення WebSocket: хто яку ставку зробив + нова ціна в грошах для показу."""
    type: str = "bid_placed"
    lot_id: int
    bidder: str
    amount: float
    start_price: float
    current_price: float
    new_bid_display: str


class TimeExtendedMessage(BaseModel):
    type: str = "time_extended"
    lot_id: int
    end_time: str

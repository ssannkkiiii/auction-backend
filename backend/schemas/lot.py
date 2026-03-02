from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from backend.db.models import LotStatus


class LotCreate(BaseModel):
    title: str
    description: str = ""
    start_price: float


class LotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    start_price: Decimal
    current_price: Decimal
    status: LotStatus
    end_time: datetime | None
    created_at: datetime


class LotListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    start_price: Decimal
    current_price: Decimal
    status: LotStatus
    end_time: datetime | None
    created_at: datetime

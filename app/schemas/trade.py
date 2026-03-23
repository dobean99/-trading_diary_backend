import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.trade import TradeSide


class TradeBase(BaseModel):
    symbol: str
    side: TradeSide
    quantity: float
    entry_price: float
    exit_price: float | None = None
    opened_at: datetime
    closed_at: datetime | None = None
    notes: str | None = None


class TradeCreate(TradeBase):
    pass


class TradeUpdate(BaseModel):
    symbol: str | None = None
    side: TradeSide | None = None
    quantity: float | None = None
    entry_price: float | None = None
    exit_price: float | None = None
    opened_at: datetime | None = None
    closed_at: datetime | None = None
    notes: str | None = None


class TradeRead(TradeBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

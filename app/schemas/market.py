from pydantic import BaseModel


class MarketCoinsResponse(BaseModel):
    exchange: str
    quote: str
    total: int
    symbols: list[str]


class MarketPriceItem(BaseModel):
    symbol: str
    price: float | None
    change_24h_pct: float | None


class MarketPricesResponse(BaseModel):
    exchange: str
    total: int
    items: list[MarketPriceItem]

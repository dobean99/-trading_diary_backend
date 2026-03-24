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


class FuturesPositionItem(BaseModel):
    symbol: str
    side: str | None
    contracts: float | None
    entry_price: float | None
    mark_price: float | None
    notional: float | None
    leverage: float | None
    unrealized_pnl: float | None
    pnl_percent: float | None
    liquidation_price: float | None
    timestamp: int | None
    datetime: str | None


class FuturesPositionsResponse(BaseModel):
    exchange: str
    total: int
    items: list[FuturesPositionItem]


class FuturesPositionHistoryItem(BaseModel):
    symbol: str
    position_side: str
    trade_id: str | None
    order_id: str | None
    side: str | None
    price: float | None
    amount: float | None
    delta_contracts: float | None
    contracts_after: float | None
    realized_pnl: float | None
    fee_cost: float | None
    fee_currency: str | None
    timestamp: int | None
    datetime: str | None


class FuturesPositionHistoryResponse(BaseModel):
    exchange: str
    from_time: str
    to_time: str
    total: int
    items: list[FuturesPositionHistoryItem]

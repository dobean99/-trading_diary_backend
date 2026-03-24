from typing import Any
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, HTTPException, Query, status
import ccxt.async_support as ccxt

from app.core.config import settings
from app.schemas.market import (
    FuturesPositionHistoryItem,
    FuturesPositionHistoryResponse,
    FuturesPositionItem,
    FuturesPositionsResponse,
    MarketCoinsResponse,
    MarketPriceItem,
    MarketPricesResponse,
)

router = APIRouter()


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_ms(dt: datetime) -> int:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    else:
        dt = dt.astimezone(UTC)
    return int(dt.timestamp() * 1000)


def _contracts_delta(
    side: str | None, amount: float | None, position_side: str
) -> float:
    if amount is None or amount == 0:
        return 0.0
    normalized_side = (side or "").upper()
    normalized_pos_side = (position_side or "BOTH").upper()

    if normalized_pos_side == "SHORT":
        # In hedge mode, SELL opens/increases short; BUY closes/reduces short.
        return amount if normalized_side == "SELL" else -amount

    # BOTH (one-way) and LONG in hedge mode use BUY as positive.
    return amount if normalized_side == "BUY" else -amount


async def _fetch_my_trades_range(
    client: Any,
    symbol: str,
    from_ms: int,
    to_ms: int,
    max_records: int,
) -> list[dict[str, Any]]:
    all_trades: list[dict[str, Any]] = []
    cursor = from_ms

    while cursor <= to_ms and len(all_trades) < max_records:
        remaining = max_records - len(all_trades)
        batch_limit = min(1000, remaining)

        batch = await client.fetch_my_trades(
            symbol=symbol,
            since=cursor,
            limit=batch_limit,
            params={"endTime": to_ms},
        )
        if not batch:
            break

        valid_batch = [
            trade
            for trade in batch
            if trade.get("timestamp") is not None
            and from_ms <= trade["timestamp"] <= to_ms
        ]
        all_trades.extend(valid_batch)

        last_ts = batch[-1].get("timestamp")
        if last_ts is None:
            break

        next_cursor = int(last_ts) + 1
        if next_cursor <= cursor:
            break
        cursor = next_cursor

        if len(batch) < batch_limit:
            break

    return all_trades[:max_records]


@router.get("/coins", response_model=MarketCoinsResponse)
async def list_coins(
    exchange: str = Query(default="binance", min_length=2, max_length=30),
    quote: str = Query(default="USDT", min_length=2, max_length=10),
    spot_only: bool = Query(default=True),
    active_only: bool = Query(default=True),
    sort: str = Query(default="volume_desc", pattern="^(volume_desc|alpha)$"),
    limit: int = Query(default=200, ge=1, le=2000),
) -> MarketCoinsResponse:
    exchange_id = exchange.lower()
    quote_currency = quote.upper()

    if exchange_id not in ccxt.exchanges:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported exchange: {exchange_id}",
        )

    exchange_class = getattr(ccxt, exchange_id)
    client = exchange_class({"enableRateLimit": True})

    try:
        markets = await client.load_markets()
    except Exception as exc:
        await client.close()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to load markets from {exchange_id}",
        ) from exc

    symbols: list[str] = []
    for symbol, market in markets.items():
        if spot_only and not market.get("spot"):
            continue
        if active_only and not market.get("active"):
            continue
        if market.get("quote") != quote_currency:
            continue
        symbols.append(symbol)

    if sort == "volume_desc":
        try:
            tickers = await client.fetch_tickers(symbols)
        except Exception:
            tickers = {}

        def volume_value(symbol: str) -> float:
            ticker: dict[str, Any] | None = tickers.get(symbol)
            if not ticker:
                return 0.0
            raw = ticker.get("quoteVolume")
            if raw is None:
                raw = ticker.get("baseVolume")
            try:
                return float(raw or 0)
            except (TypeError, ValueError):
                return 0.0

        symbols.sort(key=volume_value, reverse=True)
    else:
        symbols.sort()

    symbols = symbols[:limit]
    await client.close()

    return MarketCoinsResponse(
        exchange=exchange_id,
        quote=quote_currency,
        total=len(symbols),
        symbols=symbols,
    )


@router.get("/prices", response_model=MarketPricesResponse)
async def list_prices(
    exchange: str = Query(default="binance", min_length=2, max_length=30),
    quote: str = Query(default="USDT", min_length=2, max_length=10),
    symbols: list[str] | None = Query(default=None),
    spot_only: bool = Query(default=True),
    active_only: bool = Query(default=True),
    limit: int = Query(default=100, ge=1, le=500),
) -> MarketPricesResponse:
    exchange_id = exchange.lower()
    quote_currency = quote.upper()

    if exchange_id not in ccxt.exchanges:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported exchange: {exchange_id}",
        )

    exchange_class = getattr(ccxt, exchange_id)
    client = exchange_class({"enableRateLimit": True})

    try:
        markets = await client.load_markets()
    except Exception as exc:
        await client.close()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to load markets from {exchange_id}",
        ) from exc

    symbols_explicit = bool(symbols)
    if symbols_explicit:
        requested_symbols = [
            symbol.strip().upper() for symbol in symbols if symbol.strip()
        ]
        candidate_symbols = [
            symbol for symbol in requested_symbols if symbol in markets
        ]
    else:
        candidate_symbols = []
        for symbol, market in markets.items():
            if spot_only and not market.get("spot"):
                continue
            if active_only and not market.get("active"):
                continue
            if market.get("quote") != quote_currency:
                continue
            candidate_symbols.append(symbol)
        candidate_symbols.sort()

    candidate_symbols = candidate_symbols[:limit]
    if not candidate_symbols:
        await client.close()
        return MarketPricesResponse(exchange=exchange_id, total=0, items=[])

    try:
        tickers = await client.fetch_tickers(candidate_symbols)
    except Exception:
        tickers = {}
        for symbol in candidate_symbols:
            try:
                tickers[symbol] = await client.fetch_ticker(symbol)
            except Exception:
                continue
    finally:
        await client.close()

    items: list[MarketPriceItem] = []
    for symbol in candidate_symbols:
        ticker = tickers.get(symbol)
        if ticker is None:
            continue

        price = ticker.get("last")
        change_24h_pct = ticker.get("percentage")
        if change_24h_pct is None:
            open_price = ticker.get("open")
            if price is not None and open_price not in (None, 0):
                change_24h_pct = ((price - open_price) / open_price) * 100

        items.append(
            MarketPriceItem(
                symbol=symbol,
                price=price,
                change_24h_pct=change_24h_pct,
            )
        )

    if not symbols_explicit:
        items.sort(
            key=lambda item: float(
                tickers.get(item.symbol, {}).get("quoteVolume") or 0
            ),
            reverse=True,
        )

    return MarketPricesResponse(
        exchange=exchange_id,
        total=len(items),
        items=items,
    )


@router.get("/futures/positions", response_model=FuturesPositionsResponse)
async def get_futures_positions(
    include_zero: bool = Query(default=False),
) -> FuturesPositionsResponse:
    if not settings.api_key or not settings.api_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="API_KEY or API_SECRET is missing in environment configuration",
        )

    client = ccxt.binanceusdm(
        {
            "apiKey": settings.api_key,
            "secret": settings.api_secret,
            "enableRateLimit": True,
            "options": {"defaultType": "future"},
        }
    )

    try:
        positions = await client.fetch_positions()
        # balance = await positions.fetch_balance()
        # print(balance["info"])
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to fetch Binance futures positions",
        ) from exc
    finally:
        await client.close()

    items: list[FuturesPositionItem] = []
    for position in positions:
        contracts = _to_float(position.get("contracts"))
        if not include_zero and (contracts is None or contracts == 0):
            continue

        items.append(
            FuturesPositionItem(
                symbol=position.get("symbol", ""),
                side=position.get("side"),
                contracts=contracts,
                entry_price=_to_float(position.get("entryPrice")),
                mark_price=_to_float(position.get("markPrice")),
                notional=_to_float(position.get("notional")),
                leverage=_to_float(position.get("leverage")),
                unrealized_pnl=_to_float(position.get("unrealizedPnl")),
                pnl_percent=_to_float(position.get("percentage")),
                liquidation_price=_to_float(position.get("liquidationPrice")),
                timestamp=position.get("timestamp"),
                datetime=position.get("datetime"),
            )
        )

    return FuturesPositionsResponse(
        exchange="binanceusdm",
        total=len(items),
        items=items,
    )


@router.get("/futures/positions/history", response_model=FuturesPositionHistoryResponse)
async def get_futures_positions_history(
    symbols: list[str] = Query(
        ..., description="Repeat query param: symbols=BTC/USDT&symbols=ETH/USDT"
    ),
    from_time: datetime | None = Query(default=None),
    to_time: datetime | None = Query(default=None),
    max_records_per_symbol: int = Query(default=2000, ge=1, le=10000),
) -> FuturesPositionHistoryResponse:
    if not settings.api_key or not settings.api_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="API_KEY or API_SECRET is missing in environment configuration",
        )

    end_dt = to_time or datetime.now(UTC)
    start_dt = from_time or (end_dt - timedelta(days=360))
    if start_dt >= end_dt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="from_time must be earlier than to_time",
        )

    from_ms = _to_ms(start_dt)
    to_ms = _to_ms(end_dt)

    client = ccxt.binanceusdm(
        {
            "apiKey": settings.api_key,
            "secret": settings.api_secret,
            "enableRateLimit": True,
            "options": {"defaultType": "future"},
        }
    )

    try:
        await client.load_markets()
    except Exception as exc:
        await client.close()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to load Binance futures markets",
        ) from exc

    target_symbols = []
    for symbol in symbols:
        normalized = symbol.strip().upper()
        if normalized and normalized in client.markets:
            target_symbols.append(normalized)
    if not target_symbols:
        await client.close()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid futures symbols provided",
        )

    trade_events: list[dict[str, Any]] = []
    try:
        for symbol in target_symbols:
            trades = await _fetch_my_trades_range(
                client=client,
                symbol=symbol,
                from_ms=from_ms,
                to_ms=to_ms,
                max_records=max_records_per_symbol,
            )
            trade_events.extend(trades)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to fetch Binance futures trade history",
        ) from exc
    finally:
        await client.close()

    trade_events.sort(
        key=lambda t: (int(t.get("timestamp") or 0), str(t.get("id") or ""))
    )

    running_contracts: dict[tuple[str, str], float] = {}
    items: list[FuturesPositionHistoryItem] = []
    for trade in trade_events:
        symbol = trade.get("symbol") or ""
        info = trade.get("info") or {}
        position_side = str(info.get("positionSide") or "BOTH").upper()
        side = trade.get("side")
        amount = _to_float(trade.get("amount"))
        delta = _contracts_delta(side=side, amount=amount, position_side=position_side)

        key = (symbol, position_side)
        contracts_after = running_contracts.get(key, 0.0) + delta
        running_contracts[key] = contracts_after

        fee = trade.get("fee") or {}
        items.append(
            FuturesPositionHistoryItem(
                symbol=symbol,
                position_side=position_side,
                trade_id=str(trade.get("id")) if trade.get("id") is not None else None,
                order_id=(
                    str(trade.get("order")) if trade.get("order") is not None else None
                ),
                side=side.upper() if isinstance(side, str) else None,
                price=_to_float(trade.get("price")),
                amount=amount,
                delta_contracts=delta,
                contracts_after=contracts_after,
                realized_pnl=_to_float(info.get("realizedPnl")),
                fee_cost=_to_float(fee.get("cost")),
                fee_currency=fee.get("currency"),
                timestamp=trade.get("timestamp"),
                datetime=trade.get("datetime"),
            )
        )

    return FuturesPositionHistoryResponse(
        exchange="binanceusdm",
        from_time=start_dt.astimezone(UTC).isoformat(),
        to_time=end_dt.astimezone(UTC).isoformat(),
        total=len(items),
        items=items,
    )

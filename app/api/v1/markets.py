from fastapi import APIRouter, HTTPException, Query, status
import ccxt.async_support as ccxt

from app.schemas.market import MarketCoinsResponse, MarketPriceItem, MarketPricesResponse

router = APIRouter()


@router.get("/coins", response_model=MarketCoinsResponse)
async def list_coins(
    exchange: str = Query(default="binance", min_length=2, max_length=30),
    quote: str = Query(default="USDT", min_length=2, max_length=10),
    spot_only: bool = Query(default=True),
    active_only: bool = Query(default=True),
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
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to load markets from {exchange_id}",
        ) from exc
    finally:
        await client.close()

    symbols: list[str] = []
    for symbol, market in markets.items():
        if spot_only and not market.get("spot"):
            continue
        if active_only and not market.get("active"):
            continue
        if market.get("quote") != quote_currency:
            continue
        symbols.append(symbol)

    symbols.sort()
    symbols = symbols[:limit]

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
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to load markets from {exchange_id}",
        ) from exc

    if symbols:
        requested_symbols = [symbol.strip().upper() for symbol in symbols if symbol.strip()]
        candidate_symbols = [symbol for symbol in requested_symbols if symbol in markets]
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

    return MarketPricesResponse(
        exchange=exchange_id,
        total=len(items),
        items=items,
    )

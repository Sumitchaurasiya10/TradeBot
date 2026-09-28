from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
import pytz

from backend.app.core.config import settings
from backend.app.schemas.market import (
    DataStatus,
    IndexQuote,
    Quote,
)
from backend.app.services.market_cache import LiveMarketCache, market_cache
from backend.app.services.market_data import get_market_data_provider
from backend.app.services.market_data.base import MarketDataProvider
from backend.app.services.market_status import MarketSessionStatus, MarketStatusService

IST = pytz.timezone("Asia/Kolkata")
router = APIRouter()


@router.get("/status", response_model=MarketSessionStatus, summary="Get Live Market Session Status")
async def get_market_status():
    """
    Returns current NSE/BSE trading session status, hours, and next open/close timestamps.
    Strictly localized to Asia/Kolkata timezone.
    """
    return MarketStatusService.get_status()


@router.get("/indices", response_model=List[IndexQuote], summary="Get Major Benchmark Indices")
async def get_benchmark_indices(
    force_refresh: bool = False,
    provider: MarketDataProvider = Depends(get_market_data_provider),
):
    """
    Returns live or cached quotes for NIFTY 50, SENSEX, and BANK NIFTY.
    """
    if not force_refresh:
        cached = await market_cache.get_all_indices()
        if len(cached) >= 3:
            return cached

    indices = await provider.get_indices_quotes()
    await market_cache.set_indices_quotes(indices)
    return indices


@router.get("/quotes", response_model=List[Quote], summary="Get Live Equity Quotes for Watchlist")
async def get_equity_quotes(
    symbols: Optional[str] = Query(
        None, description="Comma-separated symbols, e.g. 'RELIANCE,TCS,INFY'. Defaults to all 8 core equities."
    ),
    force_refresh: bool = False,
    provider: MarketDataProvider = Depends(get_market_data_provider),
):
    """
    Returns quotes for equities with LTP, Day High/Low, Previous Close, Volume, and Bid/Ask.
    """
    if symbols:
        target_symbols = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    else:
        target_symbols = [
            s.replace(".NS", "") for s in settings.SUPPORTED_SYMBOLS
        ]

    if not force_refresh:
        cached_quotes = []
        missing_symbols = []
        for sym in target_symbols:
            cached = await market_cache.get_quote(sym)
            if cached and cached.data_status != DataStatus.STALE:
                cached_quotes.append(cached)
            else:
                missing_symbols.append(sym)

        if not missing_symbols:
            return cached_quotes

        # Fetch only missing
        fetched = await provider.get_quotes(missing_symbols)
        await market_cache.set_quotes(fetched)
        all_res = {q.symbol: q for q in (cached_quotes + fetched)}
        return [all_res[s] for s in target_symbols if s in all_res]

    quotes = await provider.get_quotes(target_symbols)
    await market_cache.set_quotes(quotes)
    return quotes


@router.get("/quotes/{symbol}", response_model=Quote, summary="Get Single Symbol Quote")
async def get_single_quote(
    symbol: str,
    force_refresh: bool = False,
    provider: MarketDataProvider = Depends(get_market_data_provider),
):
    """
    Returns detailed quote for a single equity symbol.
    """
    clean = symbol.upper().replace(".NS", "").strip()

    if not force_refresh:
        cached = await market_cache.get_quote(clean)
        if cached and cached.data_status != DataStatus.STALE:
            return cached

    quote = await provider.get_quote(clean)
    await market_cache.set_quote(quote)
    return quote


@router.get("/history/{symbol}", summary="Get Multi-Timeframe Historical / Intraday Chart Data")
async def get_symbol_chart_history(
    symbol: str,
    timeframe: str = Query("1M", description="Chart timeframe: 1D, 5D, 1M, 3M, 6M, 1Y"),
    provider: MarketDataProvider = Depends(get_market_data_provider),
):
    """
    Returns historical price action bars for interactive charting in 1D, 5D, 1M, 3M, 6M, 1Y timeframes.
    """
    clean = symbol.upper().replace(".NS", "").strip()
    now = datetime.now(IST)
    tf = timeframe.upper().strip()

    interval = "1d"
    if tf == "1D":
        start_date = now - timedelta(days=2)
        interval = "1d"
    elif tf == "5D":
        start_date = now - timedelta(days=7)
        interval = "1d"
    elif tf == "1M":
        start_date = now - timedelta(days=32)
        interval = "1d"
    elif tf == "3M":
        start_date = now - timedelta(days=93)
        interval = "1d"
    elif tf == "6M":
        start_date = now - timedelta(days=186)
        interval = "1d"
    elif tf == "1Y":
        start_date = now - timedelta(days=366)
        interval = "1d"
    else:
        start_date = now - timedelta(days=32)
        interval = "1d"

    df = await provider.get_historical_data(clean, start_date=start_date, interval=interval)

    bars = []
    if df is not None and not df.empty:
        for _, row in df.iterrows():
            ts = row["timestamp"]
            ts_str = ts.isoformat() if hasattr(ts, "isoformat") else str(ts)
            bars.append({
                "timestamp": ts_str,
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": int(row["volume"]),
            })

    return {
        "symbol": clean,
        "timeframe": tf,
        "interval": interval,
        "data_status": DataStatus.HISTORICAL,
        "count": len(bars),
        "bars": bars,
    }
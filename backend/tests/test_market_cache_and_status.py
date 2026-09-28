from datetime import datetime, timezone, timedelta
from decimal import Decimal
import pytest
import pytz

from backend.app.schemas.market import (
    AssetType,
    DataStatus,
    IndexQuote,
    OptionChainResponse,
    Quote,
)
from backend.app.services.market_cache import LiveMarketCache
from backend.app.services.market_status import MarketSession, MarketStatusService

IST = pytz.timezone("Asia/Kolkata")


def test_market_status_pre_open():
    # Tuesday at 09:05 AM IST
    sim_time = IST.localize(datetime(2026, 9, 29, 9, 5, 0))
    status = MarketStatusService.get_status(sim_time)
    assert status.session == MarketSession.PRE_OPEN
    assert status.is_open is False
    assert "Pre-market" in status.message


def test_market_status_market_open():
    # Wednesday at 11:30 AM IST
    sim_time = IST.localize(datetime(2026, 9, 30, 11, 30, 0))
    status = MarketStatusService.get_status(sim_time)
    assert status.session == MarketSession.MARKET_OPEN
    assert status.is_open is True
    assert "Live continuous" in status.message


def test_market_status_post_market():
    # Thursday at 15:45 IST
    sim_time = IST.localize(datetime(2026, 10, 1, 15, 45, 0))
    status = MarketStatusService.get_status(sim_time)
    assert status.session == MarketSession.POST_MARKET
    assert status.is_open is False


def test_market_status_evening_closed():
    # Friday at 20:00 IST (Markets closed, next open is Monday)
    sim_time = IST.localize(datetime(2026, 10, 2, 20, 0, 0))
    status = MarketStatusService.get_status(sim_time)
    assert status.session == MarketSession.MARKET_CLOSED
    assert status.is_open is False
    assert status.next_open_time is not None
    assert "2026-10-05 09:15:00" in status.next_open_time


def test_market_status_weekend():
    # Sunday at 14:00 IST
    sim_time = IST.localize(datetime(2026, 10, 4, 14, 0, 0))
    status = MarketStatusService.get_status(sim_time)
    assert status.session == MarketSession.MARKET_CLOSED
    assert status.is_open is False
    assert "Weekend" in status.message


@pytest.mark.asyncio
async def test_cache_set_and_get_quote():
    cache = LiveMarketCache(stale_threshold_seconds=30)
    now = datetime.now(IST)

    q = Quote(
        symbol="TCS",
        exchange="NSE",
        asset_type=AssetType.EQUITY,
        timestamp=now,
        last_price=Decimal("3500.00"),
        volume=100000,
        data_status=DataStatus.LIVE,
    )
    await cache.set_quote(q)

    retrieved = await cache.get_quote("TCS")
    assert retrieved is not None
    assert retrieved.symbol == "TCS"
    assert retrieved.last_price == Decimal("3500.00")
    assert retrieved.data_status == DataStatus.LIVE

    # Normalize check with .NS
    retrieved_ns = await cache.get_quote("TCS.NS")
    assert retrieved_ns is not None
    assert retrieved_ns.symbol == "TCS"


@pytest.mark.asyncio
async def test_cache_staleness_detection():
    cache = LiveMarketCache(stale_threshold_seconds=5)  # 5 sec threshold
    past_time = datetime.now(timezone.utc) - timedelta(seconds=15)

    q = Quote(
        symbol="INFY",
        exchange="NSE",
        asset_type=AssetType.EQUITY,
        timestamp=past_time,
        last_price=Decimal("1500.00"),
        volume=200000,
        data_status=DataStatus.LIVE,
    )
    await cache.set_quote(q)

    # Retrieval should mark it as STALE because it is 15s old and threshold is 5s
    retrieved = await cache.get_quote("INFY")
    assert retrieved is not None
    assert retrieved.data_status == DataStatus.STALE


@pytest.mark.asyncio
async def test_cache_indices_and_clear():
    cache = LiveMarketCache()
    now = datetime.now(IST)

    idx = IndexQuote(
        symbol="NIFTY 50",
        exchange="NSE",
        timestamp=now,
        last_price=Decimal("25000.00"),
        data_status=DataStatus.LIVE,
    )
    await cache.set_index_quote(idx)

    retrieved = await cache.get_index_quote("NIFTY 50")
    assert retrieved is not None
    assert retrieved.last_price == Decimal("25000.00")

    indices = await cache.get_all_indices()
    assert len(indices) == 1

    await cache.clear()
    assert await cache.get_index_quote("NIFTY 50") is None
    assert len(await cache.get_all_quotes()) == 0
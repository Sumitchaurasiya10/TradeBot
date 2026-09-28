import pytest
from httpx import ASGITransport, AsyncClient

from backend.app.main import app
from backend.app.schemas.market import DataStatus
from backend.app.services.market_cache import market_cache
from backend.app.services.market_data import reset_market_data_provider
from backend.app.services.market_data.mock_provider import MockLiveMarketDataProvider


@pytest.fixture(autouse=True)
def setup_mock_market_data():
    mock_p = MockLiveMarketDataProvider()
    reset_market_data_provider(mock_p)
    yield
    reset_market_data_provider()


@pytest.mark.asyncio
async def test_api_market_status():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/v1/market/status")
        assert res.status_code == 200
        data = res.json()
        assert "session" in data
        assert "is_open" in data
        assert "current_time_ist" in data
        assert data["timezone"] == "Asia/Kolkata"


@pytest.mark.asyncio
async def test_api_market_indices():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/v1/market/indices")
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 3
        symbols = [idx["symbol"] for idx in data]
        assert "NIFTY 50" in symbols
        assert "SENSEX" in symbols
        assert "BANK NIFTY" in symbols

        for item in data:
            assert float(item["last_price"]) > 0


@pytest.mark.asyncio
async def test_api_market_quotes_default_watchlist():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/v1/market/quotes")
        assert res.status_code == 200
        quotes = res.json()
        assert len(quotes) >= 5
        syms = [q["symbol"] for q in quotes]
        assert "RELIANCE" in syms
        assert "TCS" in syms
        assert "INFY" in syms


@pytest.mark.asyncio
async def test_api_market_quotes_custom_symbols():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/v1/market/quotes?symbols=TCS,INFY")
        assert res.status_code == 200
        quotes = res.json()
        assert len(quotes) == 2
        syms = [q["symbol"] for q in quotes]
        assert "TCS" in syms
        assert "INFY" in syms


@pytest.mark.asyncio
async def test_api_market_single_quote():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/v1/market/quotes/RELIANCE")
        assert res.status_code == 200
        data = res.json()
        assert data["symbol"] == "RELIANCE"
        assert float(data["last_price"]) > 0
        assert data["exchange"] == "NSE"


@pytest.mark.asyncio
async def test_api_market_history_chart():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/v1/market/history/TCS?timeframe=1M")
        assert res.status_code == 200
        data = res.json()
        assert data["symbol"] == "TCS"
        assert data["timeframe"] == "1M"
        assert len(data["bars"]) > 0
        first_bar = data["bars"][0]
        assert "open" in first_bar
        assert "close" in first_bar
        assert "timestamp" in first_bar
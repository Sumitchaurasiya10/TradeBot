from decimal import Decimal
import pytest
from httpx import ASGITransport, AsyncClient
from backend.app.database.init_db import init_db
from backend.app.main import app
from backend.app.services.data_ingestion import DataIngestionService
from backend.app.services.data_provider import MockDataProvider


@pytest.fixture(autouse=True)
def setup_mock_provider(monkeypatch):
    """
    Ensure all API tests run offline using MockDataProvider
    to avoid slow or throttled external network requests.
    """
    mock_provider = MockDataProvider()
    from backend.app.api.v1.endpoints import backtest, stocks, strategy
    stocks.ingestion_service = DataIngestionService(default_provider=mock_provider)
    strategy.ingestion_service = DataIngestionService(default_provider=mock_provider)
    backtest.ingestion_service = DataIngestionService(default_provider=mock_provider)


@pytest.mark.asyncio
async def test_root_healthcheck():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "HEALTHY"
        assert "Paper" in data["disclaimer"]


@pytest.mark.asyncio
async def test_bot_status_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/bot/status")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ONLINE"
        assert data["paper_trading_mode"] is True
        assert data["real_money_trading"] is False
        assert "RELIANCE.NS" in data["supported_symbols"]


@pytest.mark.asyncio
async def test_get_stocks_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/stocks")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 5
        symbols = [s["symbol"] for s in data]
        assert "TCS.NS" in symbols
        assert "INFY.NS" in symbols


@pytest.mark.asyncio
async def test_get_market_data_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/stocks/TCS.NS/market-data")
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "TCS.NS"
        assert data["count"] >= 20
        assert len(data["bars"]) >= 20
        assert "open" in data["bars"][0]
        assert "close" in data["bars"][0]


@pytest.mark.asyncio
async def test_get_indicators_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/stocks/TCS.NS/indicators?fast_ema=5&slow_ema=10")
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "TCS.NS"
        assert len(data["bars"]) >= 20
        last_bar = data["bars"][-1]
        assert last_bar["fast_ema"] is not None
        assert last_bar["slow_ema"] is not None
        assert last_bar["rsi"] is not None


@pytest.mark.asyncio
async def test_strategy_signal_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "symbol": "TCS.NS",
            "fast_ema_period": 5,
            "slow_ema_period": 10,
            "rsi_period": 5,
            "rsi_entry_threshold": 45.0,
            "volume_ma_period": 5,
            "volume_multiplier": 0.5,
        }
        response = await client.post("/api/v1/strategy/signal", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "TCS.NS"
        assert data["signal"] in ["BUY", "SELL", "HOLD"]
        assert len(data["reason"]) > 0
        assert "fast_ema" in data["indicators"]


@pytest.mark.asyncio
async def test_backtest_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "symbol": "INFY.NS",
            "initial_capital": 100000.0,
            "fast_ema_period": 5,
            "slow_ema_period": 10,
            "rsi_period": 5,
            "rsi_entry_threshold": 45.0,
            "volume_ma_period": 5,
            "volume_multiplier": 0.5,
        }
        response = await client.post("/api/v1/backtest", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "INFY.NS"
        assert data["initial_capital"] == 100000.0
        assert "total_return_pct" in data
        assert "benchmark_return_pct" in data
        assert len(data["equity_curve"]) > 0


@pytest.mark.asyncio
async def test_paper_trading_order_and_portfolio_endpoints():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Place a valid simulated order (5 shares @ ₹1000 = 5000 <= 20000)
        order_payload = {
            "symbol": "HDFCBANK.NS",
            "side": "BUY",
            "quantity": 5,
            "price": 1000.0,
        }
        order_res = await client.post("/api/v1/paper/orders", json=order_payload)
        assert order_res.status_code == 200
        order_data = order_res.json()
        assert order_data["status"] == "FILLED"
        assert order_data["symbol"] == "HDFCBANK.NS"

        # 2. Get Portfolio
        port_res = await client.get("/api/v1/paper/portfolio")
        assert port_res.status_code == 200
        port_data = port_res.json()
        assert port_data["currency"] == "INR"
        assert port_data["open_positions_count"] >= 1

        # 3. Get Positions
        pos_res = await client.get("/api/v1/paper/positions")
        assert pos_res.status_code == 200
        pos_data = pos_res.json()
        symbols = [p["symbol"] for p in pos_data]
        assert "HDFCBANK.NS" in symbols

        # 4. Get PnL
        pnl_res = await client.get("/api/v1/paper/pnl")
        assert pnl_res.status_code == 200
        pnl_data = pnl_res.json()
        assert "realized_pnl" in pnl_data
        assert "total_equity" in pnl_data

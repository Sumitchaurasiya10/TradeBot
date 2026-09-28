import pytest
from httpx import ASGITransport, AsyncClient

from backend.app.main import app
from backend.app.schemas.strategy import SignalResponse
from backend.app.services.live_strategy_evaluator import LiveStrategyEvaluator
from backend.app.services.market_data import reset_market_data_provider
from backend.app.services.market_data.mock_provider import MockLiveMarketDataProvider


@pytest.fixture(autouse=True)
def setup_mock_market_data():
    mock_p = MockLiveMarketDataProvider()
    reset_market_data_provider(mock_p)
    yield
    reset_market_data_provider()


@pytest.mark.asyncio
async def test_live_strategy_evaluator_direct():
    mock_p = MockLiveMarketDataProvider()
    res = await LiveStrategyEvaluator.evaluate_live_signal(
        symbol="RELIANCE",
        provider=mock_p,
        fast_ema=9,
        slow_ema=21,
        rsi_period=14,
    )
    assert isinstance(res, SignalResponse)
    assert res.symbol == "RELIANCE"
    assert res.signal in ["BUY", "SELL", "HOLD"]
    assert "fast_ema" in res.indicators
    assert "slow_ema" in res.indicators
    assert "rsi" in res.indicators
    assert len(res.reason) > 5


@pytest.mark.asyncio
async def test_api_get_live_signal_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/v1/strategy/live-signal/TCS?fast_ema=9&slow_ema=21")
        assert res.status_code == 200
        data = res.json()
        assert data["symbol"] == "TCS"
        assert data["signal"] in ["BUY", "SELL", "HOLD"]
        assert data["parameters"]["fast_ema_period"] == 9
        assert data["parameters"]["slow_ema_period"] == 21


@pytest.mark.asyncio
async def test_api_get_live_signal_invalid_params():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # fast_ema >= slow_ema must be rejected
        res = await client.get("/api/v1/strategy/live-signal/TCS?fast_ema=25&slow_ema=10")
        assert res.status_code == 400


@pytest.mark.asyncio
async def test_paper_trading_auto_price_and_live_position_update():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Place buy order with price=0 (auto-fill from live quote)
        order_payload = {
            "symbol": "INFY",
            "side": "BUY",
            "quantity": 5,
            "price": 0.0,  # Auto-fetch live price
        }
        res_order = await client.post("/api/v1/paper/orders", json=order_payload)
        assert res_order.status_code == 200
        order_data = res_order.json()
        assert order_data["status"] == "FILLED"
        assert float(order_data["executed_price"]) > 0

        # Query portfolio - should reflect open position with live pricing
        res_port = await client.get("/api/v1/paper/portfolio")
        assert res_port.status_code == 200
        port_data = res_port.json()
        assert port_data["open_positions_count"] >= 1

        infy_pos = next((p for p in port_data["positions"] if "INFY" in p["symbol"]), None)
        assert infy_pos is not None
        assert infy_pos["quantity"] == 5
        assert float(infy_pos["current_price"]) > 0
        assert "unrealized_pnl" in infy_pos
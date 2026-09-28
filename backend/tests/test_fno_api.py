import pytest
from httpx import ASGITransport, AsyncClient

from backend.app.main import app
from backend.app.services.market_data import reset_market_data_provider
from backend.app.services.market_data.mock_provider import MockLiveMarketDataProvider


@pytest.fixture(autouse=True)
def setup_mock_market_data():
    mock_p = MockLiveMarketDataProvider()
    reset_market_data_provider(mock_p)
    yield
    reset_market_data_provider()


@pytest.mark.asyncio
async def test_api_fno_underlyings():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/v1/fno/underlyings")
        assert res.status_code == 200
        data = res.json()
        assert len(data) >= 4
        symbols = [u["underlying"] for u in data]
        assert "NIFTY" in symbols
        assert "BANK NIFTY" in symbols
        assert "RELIANCE" in symbols


@pytest.mark.asyncio
async def test_api_fno_expiries():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/v1/fno/expiries/NIFTY")
        assert res.status_code == 200
        expiries = res.json()
        assert len(expiries) >= 2
        # Verify date format YYYY-MM-DD
        for exp in expiries:
            assert len(exp.split("-")) == 3


@pytest.mark.asyncio
async def test_api_fno_option_chain():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/v1/fno/option-chain/NIFTY")
        assert res.status_code == 200
        chain = res.json()
        assert chain["underlying"] == "NIFTY"
        assert float(chain["underlying_price"]) > 0
        assert len(chain["strikes"]) > 0

        first_strike = chain["strikes"][0]
        assert "strike_price" in first_strike
        assert "call" in first_strike
        assert "put" in first_strike
        if first_strike["call"]:
            assert "open_interest" in first_strike["call"]
            assert "last_price" in first_strike["call"]


@pytest.mark.asyncio
async def test_api_fno_contracts_list():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/v1/fno/contracts/BANK%20NIFTY")
        assert res.status_code == 200
        contracts = res.json()
        assert len(contracts) > 0
        assert "instrument_type" in contracts[0]
        assert "expiry" in contracts[0]
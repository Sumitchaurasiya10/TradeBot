from decimal import Decimal
import pytest
from backend.app.schemas.market import (
    AssetType,
    DataStatus,
    FNOQuote,
    IndexQuote,
    InstrumentType,
    OptionChainResponse,
    OptionType,
    Quote,
)
from backend.app.services.market_data import (
    get_market_data_provider,
    reset_market_data_provider,
)
from backend.app.services.market_data.base import MarketDataProvider
from backend.app.services.market_data.historical import HistoricalMarketDataProvider
from backend.app.services.market_data.mock_provider import MockLiveMarketDataProvider


@pytest.fixture
def mock_provider() -> MockLiveMarketDataProvider:
    return MockLiveMarketDataProvider()


@pytest.mark.asyncio
async def test_mock_provider_get_quote(mock_provider):
    quote = await mock_provider.get_quote("RELIANCE")
    assert isinstance(quote, Quote)
    assert quote.symbol == "RELIANCE"
    assert quote.exchange == "NSE"
    assert quote.asset_type == AssetType.EQUITY
    assert quote.data_status == DataStatus.DEMO_DATA
    assert isinstance(quote.last_price, Decimal)
    assert quote.last_price > 0
    assert quote.bid_price < quote.ask_price
    assert quote.volume > 0


@pytest.mark.asyncio
async def test_mock_provider_get_multiple_quotes(mock_provider):
    symbols = ["TCS", "INFY", "SBIN", "ITC", "LT"]
    quotes = await mock_provider.get_quotes(symbols)
    assert len(quotes) == len(symbols)
    retrieved_symbols = [q.symbol for q in quotes]
    for s in symbols:
        assert s in retrieved_symbols


@pytest.mark.asyncio
async def test_mock_provider_indices_quotes(mock_provider):
    indices = await mock_provider.get_indices_quotes()
    assert len(indices) == 3
    names = [i.symbol for i in indices]
    assert "NIFTY 50" in names
    assert "SENSEX" in names
    assert "BANK NIFTY" in names

    for idx in indices:
        assert isinstance(idx, IndexQuote)
        assert idx.last_price > 0
        assert idx.data_status == DataStatus.DEMO_DATA


@pytest.mark.asyncio
async def test_mock_provider_option_chain_structure(mock_provider):
    chain = await mock_provider.get_option_chain("NIFTY")
    assert isinstance(chain, OptionChainResponse)
    assert chain.underlying == "NIFTY"
    assert chain.underlying_price > 0
    assert len(chain.available_expiries) >= 1
    assert len(chain.strikes) > 0

    # Inspect a middle strike row
    mid_row = chain.strikes[len(chain.strikes) // 2]
    assert mid_row.strike_price > 0
    assert mid_row.call is not None
    assert mid_row.put is not None
    assert mid_row.call.option_type == OptionType.CE
    assert mid_row.put.option_type == OptionType.PE
    assert mid_row.call.open_interest > 0
    assert mid_row.put.open_interest > 0
    assert mid_row.call.data_status == DataStatus.DEMO_DATA


@pytest.mark.asyncio
async def test_mock_provider_fno_contracts_flattened(mock_provider):
    contracts = await mock_provider.get_fno_contracts("BANK NIFTY")
    assert len(contracts) > 0
    for c in contracts:
        assert isinstance(c, FNOQuote)
        assert c.underlying in ["BANK NIFTY", "BANKNIFTY"]
        assert c.last_price > 0
        assert c.expiry is not None


@pytest.mark.asyncio
async def test_historical_provider_interface():
    provider = HistoricalMarketDataProvider()
    assert provider.get_provider_name() == "yfinance"
    assert isinstance(provider, MarketDataProvider)

    # Option chain fallback should produce valid structure
    chain = await provider.get_option_chain("TCS")
    assert isinstance(chain, OptionChainResponse)
    assert chain.underlying == "TCS"
    assert len(chain.strikes) > 0


def test_provider_factory_and_reset():
    reset_market_data_provider()
    p1 = get_market_data_provider()
    assert isinstance(p1, MarketDataProvider)

    # Inject custom mock
    custom = MockLiveMarketDataProvider(tick_seed=999)
    reset_market_data_provider(custom)
    p2 = get_market_data_provider()
    assert p2 is custom

    # Reset back
    reset_market_data_provider()
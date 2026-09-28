from typing import Optional
from backend.app.core.config import settings
from backend.app.services.market_data.base import MarketDataProvider
from backend.app.services.market_data.historical import HistoricalMarketDataProvider
from backend.app.services.market_data.live_base import LiveMarketDataProvider
from backend.app.services.market_data.mock_provider import MockLiveMarketDataProvider

_provider_instance: Optional[MarketDataProvider] = None


def get_market_data_provider() -> MarketDataProvider:
    """
    Factory function returning the active MarketDataProvider based on configuration.
    Cached singleton for efficient connection reuse.
    """
    global _provider_instance
    if _provider_instance is None:
        provider_type = getattr(settings, "LIVE_DATA_PROVIDER", "hybrid").lower()
        if provider_type == "mock":
            _provider_instance = MockLiveMarketDataProvider()
        else:
            _provider_instance = HistoricalMarketDataProvider()
    return _provider_instance


def reset_market_data_provider(provider: Optional[MarketDataProvider] = None) -> None:
    """Helper for testing to inject custom mock providers."""
    global _provider_instance
    _provider_instance = provider
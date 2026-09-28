from abc import abstractmethod
from typing import AsyncGenerator, Dict, List, Optional
from backend.app.schemas.market import FNOQuote, IndexQuote, OptionChainResponse, Quote
from backend.app.services.market_data.base import MarketDataProvider


class LiveMarketDataProvider(MarketDataProvider):
    """
    Abstract extension of MarketDataProvider for live/streaming capabilities.
    Supports real-time tick streaming, order-book depth, and subscription management.
    """

    @abstractmethod
    async def subscribe_symbols(self, symbols: List[str]) -> bool:
        """Subscribe to real-time updates for a list of instruments."""
        pass

    @abstractmethod
    async def unsubscribe_symbols(self, symbols: List[str]) -> bool:
        """Unsubscribe from real-time updates."""
        pass

    @abstractmethod
    async def stream_quotes(self) -> AsyncGenerator[Quote, None]:
        """Yield real-time incoming quotes as an asynchronous generator."""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if WebSocket or live connection is active."""
        pass
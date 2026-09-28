from abc import ABC, abstractmethod
from datetime import datetime
from typing import AsyncGenerator, List, Optional
import pandas as pd
from backend.app.schemas.market import FNOQuote, IndexQuote, OptionChainResponse, Quote


class MarketDataProvider(ABC):
    """
    Unified abstract interface for all market data sources:
    Equities, Indices, F&O contracts, and Historical Time-Series.
    Decouples UI and Trading logic from specific APIs.
    """

    @abstractmethod
    def get_provider_name(self) -> str:
        """Returns provider identifier (e.g. 'yfinance', 'nse_public', 'mock', 'angel_one')."""
        pass

    @abstractmethod
    async def get_quote(self, symbol: str) -> Quote:
        """Fetch current quote for an equity ticker."""
        pass

    @abstractmethod
    async def get_quotes(self, symbols: List[str]) -> List[Quote]:
        """Fetch quotes for multiple equity tickers."""
        pass

    @abstractmethod
    async def get_index_quote(self, symbol: str) -> IndexQuote:
        """Fetch current points for an index (e.g. 'NIFTY 50', 'SENSEX', 'BANK NIFTY')."""
        pass

    @abstractmethod
    async def get_indices_quotes(self) -> List[IndexQuote]:
        """Fetch all primary benchmark indices."""
        pass

    @abstractmethod
    async def get_fno_contracts(self, underlying: str) -> List[FNOQuote]:
        """Fetch active Futures and Options contracts for an underlying."""
        pass

    @abstractmethod
    async def get_option_chain(
        self, underlying: str, expiry: Optional[str] = None
    ) -> OptionChainResponse:
        """Fetch strike-by-strike Option Chain (CE & PE) for an underlying."""
        pass

    @abstractmethod
    async def get_historical_data(
        self,
        symbol: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        interval: str = "1d",
    ) -> pd.DataFrame:
        """
        Fetch historical OHLCV data.
        Returns DataFrame with: ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        """
        pass
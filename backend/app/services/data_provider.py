from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional
import pandas as pd


class DataProvider(ABC):
    """
    Abstract Base Class for Market Data Providers.
    Decouples data acquisition from trading and backtesting engines.
    """

    @abstractmethod
    def fetch_ohlcv(
        self,
        symbol: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        interval: str = "1d",
    ) -> pd.DataFrame:
        """
        Fetch OHLCV data for a given symbol.
        Returns a DataFrame with columns:
        ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Returns provider identifier."""
        pass


class MockDataProvider(DataProvider):
    """
    Deterministic mock data provider for offline testing and development.
    """

    def __init__(self, custom_df: Optional[pd.DataFrame] = None):
        self._custom_df = custom_df

    def get_provider_name(self) -> str:
        return "mock"

    def fetch_ohlcv(
        self,
        symbol: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        interval: str = "1d",
    ) -> pd.DataFrame:
        if self._custom_df is not None:
            return self._custom_df.copy()

        dates = pd.date_range(start="2024-01-01", periods=60, freq="D", tz="Asia/Kolkata")
        base_price = 1000.0
        records = []

        for i, dt in enumerate(dates):
            close_price = base_price + (i * 5.0) + (10.0 if i % 2 == 0 else -10.0)
            open_price = close_price - 2.0
            high_price = close_price + 8.0
            low_price = open_price - 5.0
            volume = 100000 + (i * 2000)

            records.append({
                "timestamp": dt,
                "open": round(open_price, 2),
                "high": round(high_price, 2),
                "low": round(low_price, 2),
                "close": round(close_price, 2),
                "volume": int(volume),
            })

        return pd.DataFrame(records)

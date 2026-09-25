from datetime import datetime
from typing import Optional
import pandas as pd
import yfinance as yf
from backend.app.core.logging import logger
from backend.app.services.data_provider import DataProvider


class YFinanceProvider(DataProvider):
    """
    Unofficial Yahoo Finance market data provider for educational and paper trading use.
    Subject to exchange delays (~15 min) and rate limits.
    """

    def get_provider_name(self) -> str:
        return "yfinance"

    def fetch_ohlcv(
        self,
        symbol: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        interval: str = "1d",
    ) -> pd.DataFrame:
        """
        Fetches historical OHLCV data from Yahoo Finance for Indian tickers.
        """
        clean_symbol = symbol.strip().upper()
        # Default to 1 year of history if start_date is not specified
        start_str = start_date.strftime("%Y-%m-%d") if start_date else None
        end_str = end_date.strftime("%Y-%m-%d") if end_date else None

        logger.info(f"Fetching market data for {clean_symbol} via yfinance (interval={interval})...")

        try:
            ticker = yf.Ticker(clean_symbol)
            if start_str and end_str:
                raw_df = ticker.history(start=start_str, end=end_str, interval=interval, auto_adjust=False)
            elif start_str:
                raw_df = ticker.history(start=start_str, interval=interval, auto_adjust=False)
            else:
                # Default to past 1 year of daily bars
                raw_df = ticker.history(period="1y", interval=interval, auto_adjust=False)

            if raw_df is None or raw_df.empty:
                logger.warning(f"No data returned by yfinance for symbol '{clean_symbol}'")
                return pd.DataFrame()

            # Reset index to bring Date/Datetime into a column
            raw_df = raw_df.reset_index()

            # Flatten multi-index columns if present and normalize to lowercase
            if isinstance(raw_df.columns, pd.MultiIndex):
                raw_df.columns = [str(c[0]).strip().lower() for c in raw_df.columns]
            else:
                raw_df.columns = [str(c).strip().lower() for c in raw_df.columns]

            # Standardize timestamp column name
            date_col = None
            for candidate in ["date", "datetime", "timestamp", "index"]:
                if candidate in raw_df.columns:
                    date_col = candidate
                    break

            if not date_col:
                raise ValueError(f"Expected Date/Datetime column missing in yfinance response: {raw_df.columns.tolist()}")

            raw_df = raw_df.rename(columns={date_col: "timestamp"})

            # Select and order required columns
            required_cols = ["timestamp", "open", "high", "low", "close", "volume"]
            missing = [c for c in required_cols if c not in raw_df.columns]
            if missing:
                raise ValueError(f"Missing required OHLCV columns from yfinance: {missing}")

            clean_df = raw_df[required_cols].copy()
            clean_df["volume"] = clean_df["volume"].fillna(0).astype(int)

            return clean_df

        except Exception as e:
            logger.error(f"Error fetching data from yfinance for '{clean_symbol}': {str(e)}")
            raise

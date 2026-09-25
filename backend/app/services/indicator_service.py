from typing import Optional
import numpy as np
import pandas as pd


class IndicatorService:
    """
    Pure mathematical calculations for technical indicators using vectorized Pandas/NumPy.
    Completely decoupled from database, API, and UI.
    """

    @staticmethod
    def calculate_ema(series: pd.Series, period: int) -> pd.Series:
        """
        Calculates Exponential Moving Average (EMA).
        Formula:
            alpha = 2 / (period + 1)
            EMA_t = alpha * Close_t + (1 - alpha) * EMA_(t-1)
        Implementation:
            pandas.Series.ewm(span=period, adjust=False).mean()
        """
        if period <= 0:
            raise ValueError(f"EMA period must be positive, got {period}")
        if len(series) == 0:
            return pd.Series(dtype=float)

        return series.ewm(span=period, adjust=False).mean()

    @staticmethod
    def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
        """
        Calculates Relative Strength Index (RSI) over period N (default 14).
        Formula:
            change = Close_t - Close_(t-1)
            gain = max(change, 0)
            loss = max(-change, 0)
            avg_gain = smoothed average gain (Wilder's alpha = 1 / period)
            avg_loss = smoothed average loss (Wilder's alpha = 1 / period)
            RS = avg_gain / avg_loss
            RSI = 100 - (100 / (1 + RS))
        Guaranteed to output values bounded strictly in [0, 100].
        """
        if period <= 0:
            raise ValueError(f"RSI period must be positive, got {period}")
        if len(series) < period:
            return pd.Series(np.nan, index=series.index, dtype=float)

        delta = series.diff()

        gain = delta.clip(lower=0.0)
        loss = -delta.clip(upper=0.0)

        # Wilder's smoothing using exponential moving average with alpha = 1 / period
        avg_gain = gain.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()

        rs = avg_gain / avg_loss.replace(0, np.nan)
        rsi = 100.0 - (100.0 / (1.0 + rs))

        # Handle boundary conditions using pd.Series
        boundary_fill = np.where(
            (avg_loss == 0) & (avg_gain > 0),
            100.0,
            np.where((avg_gain == 0) & (avg_loss > 0), 0.0, 50.0),
        )
        rsi = rsi.fillna(pd.Series(boundary_fill, index=series.index))

        # First `period` bars are warm-up periods
        rsi.iloc[:period] = np.nan
        return rsi

    @staticmethod
    def calculate_volume_ma(series: pd.Series, period: int = 20) -> pd.Series:
        """Calculates Simple Moving Average (SMA) of volume."""
        if period <= 0:
            raise ValueError(f"Volume MA period must be positive, got {period}")
        return series.rolling(window=period).mean()

    @classmethod
    def enrich_dataframe(
        cls,
        df: pd.DataFrame,
        fast_ema_period: int = 9,
        slow_ema_period: int = 21,
        rsi_period: int = 14,
        volume_ma_period: int = 20,
    ) -> pd.DataFrame:
        """
        Calculates all indicator columns on an OHLCV DataFrame in a single pass.
        Returns a new copy of the DataFrame with indicator columns added.
        """
        result = df.copy()
        result[f"ema_{fast_ema_period}"] = cls.calculate_ema(result["close"], fast_ema_period)
        result[f"ema_{slow_ema_period}"] = cls.calculate_ema(result["close"], slow_ema_period)
        result[f"rsi_{rsi_period}"] = cls.calculate_rsi(result["close"], rsi_period)
        result[f"volume_ma_{volume_ma_period}"] = cls.calculate_volume_ma(result["volume"], volume_ma_period)
        return result

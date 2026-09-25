from datetime import datetime, timezone
from typing import List, Optional
import pandas as pd
import pytz
from backend.app.core.config import settings


class DataValidationError(Exception):
    """Custom exception raised when market data fails validation."""
    pass


class DataValidator:
    """
    Validates and normalizes market data prior to consumption by indicators,
    strategies, and database caching.
    """

    REQUIRED_COLUMNS = ["timestamp", "open", "high", "low", "close", "volume"]

    @classmethod
    def validate_symbol(cls, symbol: str, supported_symbols: Optional[List[str]] = None) -> str:
        """Validates that the symbol is in the allowed universe."""
        allowed = supported_symbols or settings.SUPPORTED_SYMBOLS
        clean_symbol = symbol.strip().upper()
        if clean_symbol not in allowed:
            raise DataValidationError(
                f"Unsupported symbol '{clean_symbol}'. Supported universe: {allowed}"
            )
        return clean_symbol

    @classmethod
    def validate_and_normalize(
        cls,
        df: pd.DataFrame,
        symbol: str,
        target_timezone: str = "UTC",
    ) -> pd.DataFrame:
        """
        Performs strict data hygiene and normalization on an OHLCV DataFrame.
        All timestamps are standardized to UTC for robust persistence and comparison.
        """
        cls.validate_symbol(symbol)

        if df is None or df.empty:
            raise DataValidationError(f"Empty dataset received for symbol '{symbol}'.")

        # 1. Column existence check
        missing_cols = [c for c in cls.REQUIRED_COLUMNS if c not in df.columns]
        if missing_cols:
            raise DataValidationError(
                f"Dataset for '{symbol}' missing required columns: {missing_cols}"
            )

        clean_df = df[cls.REQUIRED_COLUMNS].copy()

        # 2. Check for null / NaN values
        null_counts = clean_df.isnull().sum()
        if null_counts.any():
            corrupted = null_counts[null_counts > 0].to_dict()
            raise DataValidationError(
                f"Dataset for '{symbol}' contains null values: {corrupted}"
            )

        # 3. Timezone normalization to UTC
        try:
            if not pd.api.types.is_datetime64_any_dtype(clean_df["timestamp"]):
                clean_df["timestamp"] = pd.to_datetime(clean_df["timestamp"])

            if clean_df["timestamp"].dt.tz is None:
                clean_df["timestamp"] = clean_df["timestamp"].dt.tz_localize("UTC")
            else:
                clean_df["timestamp"] = clean_df["timestamp"].dt.tz_convert("UTC")
        except Exception as e:
            raise DataValidationError(f"Timestamp normalization failed for '{symbol}': {str(e)}")

        # 4. Remove duplicate timestamps & sort chronologically
        clean_df = clean_df.drop_duplicates(subset=["timestamp"], keep="last")
        clean_df = clean_df.sort_values(by="timestamp").reset_index(drop=True)

        # 5. Invariant validations: High >= Open and High >= Close
        invalid_high = clean_df[(clean_df["high"] < clean_df["open"]) | (clean_df["high"] < clean_df["close"])]
        if not invalid_high.empty:
            bad_idx = invalid_high.index.tolist()
            raise DataValidationError(
                f"Data corruption in '{symbol}': High is lower than Open or Close at row(s): {bad_idx}"
            )

        # Low <= Open and Low <= Close
        invalid_low = clean_df[(clean_df["low"] > clean_df["open"]) | (clean_df["low"] > clean_df["close"])]
        if not invalid_low.empty:
            bad_idx = invalid_low.index.tolist()
            raise DataValidationError(
                f"Data corruption in '{symbol}': Low is higher than Open or Close at row(s): {bad_idx}"
            )

        # Volume >= 0
        invalid_volume = clean_df[clean_df["volume"] < 0]
        if not invalid_volume.empty:
            bad_idx = invalid_volume.index.tolist()
            raise DataValidationError(
                f"Data corruption in '{symbol}': Negative volume found at row(s): {bad_idx}"
            )

        # Prices must be strictly positive (> 0)
        invalid_price = clean_df[
            (clean_df["open"] <= 0) | (clean_df["high"] <= 0) |
            (clean_df["low"] <= 0) | (clean_df["close"] <= 0)
        ]
        if not invalid_price.empty:
            bad_idx = invalid_price.index.tolist()
            raise DataValidationError(
                f"Data corruption in '{symbol}': Non-positive price found at row(s): {bad_idx}"
            )

        clean_df["validated_at"] = datetime.now(timezone.utc)
        return clean_df

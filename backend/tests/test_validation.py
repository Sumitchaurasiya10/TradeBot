import pytest
import pandas as pd
from datetime import datetime
from backend.app.services.data_validator import DataValidator, DataValidationError
from backend.app.services.data_provider import MockDataProvider


def test_valid_data_passes_validation():
    mock_provider = MockDataProvider()
    df = mock_provider.fetch_ohlcv("TCS.NS")
    validated = DataValidator.validate_and_normalize(df, "TCS.NS")
    
    assert len(validated) == 60
    assert "validated_at" in validated.columns
    assert validated["high"].ge(validated["open"]).all()
    assert validated["high"].ge(validated["close"]).all()
    assert validated["low"].le(validated["open"]).all()
    assert validated["low"].le(validated["close"]).all()
    assert (validated["volume"] >= 0).all()


def test_unsupported_symbol_raises_error():
    mock_provider = MockDataProvider()
    df = mock_provider.fetch_ohlcv("INVALID_STOCK.NS")
    with pytest.raises(DataValidationError, match="Unsupported symbol"):
        DataValidator.validate_and_normalize(df, "INVALID_STOCK.NS")


def test_empty_dataframe_raises_error():
    empty_df = pd.DataFrame()
    with pytest.raises(DataValidationError, match="Empty dataset"):
        DataValidator.validate_and_normalize(empty_df, "RELIANCE.NS")


def test_corrupted_high_lower_than_open_raises_error():
    mock_provider = MockDataProvider()
    df = mock_provider.fetch_ohlcv("INFY.NS")
    # Corrupt a high price so High < Open
    df.loc[5, "high"] = df.loc[5, "open"] - 10.0
    with pytest.raises(DataValidationError, match="High is lower than Open or Close"):
        DataValidator.validate_and_normalize(df, "INFY.NS")


def test_corrupted_negative_volume_raises_error():
    mock_provider = MockDataProvider()
    df = mock_provider.fetch_ohlcv("HDFCBANK.NS")
    df.loc[10, "volume"] = -500
    with pytest.raises(DataValidationError, match="Negative volume found"):
        DataValidator.validate_and_normalize(df, "HDFCBANK.NS")


def test_duplicate_timestamps_are_deduplicated():
    mock_provider = MockDataProvider()
    df = mock_provider.fetch_ohlcv("ICICIBANK.NS")
    # Duplicate first row
    duplicate_row = df.iloc[[0]].copy()
    df_with_duplicate = pd.concat([df, duplicate_row], ignore_index=True)
    assert len(df_with_duplicate) == 61
    
    validated = DataValidator.validate_and_normalize(df_with_duplicate, "ICICIBANK.NS")
    assert len(validated) == 60

import pytest
import pandas as pd
from backend.app.services.data_provider import MockDataProvider
from backend.app.services.data_validator import DataValidator
from backend.app.strategies.base import SignalType
from backend.app.strategies.ema_rsi_volume import EMARsiVolumeStrategy


def test_strategy_parameter_validation():
    with pytest.raises(ValueError, match="fast_ema_period"):
        EMARsiVolumeStrategy(fast_ema_period=21, slow_ema_period=9)


def test_strategy_generates_structured_signal():
    provider = MockDataProvider()
    df = provider.fetch_ohlcv("TCS.NS")
    validated = DataValidator.validate_and_normalize(df, "TCS.NS")

    strategy = EMARsiVolumeStrategy(fast_ema_period=9, slow_ema_period=21)
    signal = strategy.generate_signal(validated, "TCS.NS")

    assert signal.symbol == "TCS.NS"
    assert signal.signal in [SignalType.BUY, SignalType.SELL, SignalType.HOLD]
    assert isinstance(signal.reason, str)
    assert len(signal.reason) > 0
    assert "fast_ema" in signal.indicators
    assert "slow_ema" in signal.indicators
    assert "rsi" in signal.indicators
    assert "volume" in signal.indicators


def test_strategy_generate_all_signals_returns_signals_column():
    provider = MockDataProvider()
    df = provider.fetch_ohlcv("RELIANCE.NS")
    validated = DataValidator.validate_and_normalize(df, "RELIANCE.NS")

    strategy = EMARsiVolumeStrategy(fast_ema_period=5, slow_ema_period=10)
    all_signals_df = strategy.generate_all_signals(validated, "RELIANCE.NS")

    assert "signal" in all_signals_df.columns
    assert set(all_signals_df["signal"].unique()).issubset({"BUY", "SELL", "HOLD"})
    assert len(all_signals_df) == len(validated)


def test_strategy_detects_synthetic_bullish_and_bearish_crossovers():
    """
    Constructs a deterministic sequence:
    Flat/downtrend -> Sharp upward surge with high volume (Bullish crossover) ->
    Sharp downward drop (Bearish crossover).
    """
    dates = pd.date_range("2024-01-01", periods=40, freq="D", tz="Asia/Kolkata")
    prices = [100.0 - i * 0.2 for i in range(20)] + [96.0 + i * 5.0 for i in range(10)] + [146.0 - i * 5.0 for i in range(10)]
    records = []
    for dt, p in zip(dates, prices):
        records.append({
            "timestamp": dt,
            "open": round(p - 0.5, 2),
            "high": round(p + 1.0, 2),
            "low": round(p - 1.0, 2),
            "close": round(p, 2),
            "volume": 200000,
        })
    df = pd.DataFrame(records)
    strategy = EMARsiVolumeStrategy(
        fast_ema_period=3,
        slow_ema_period=7,
        rsi_period=5,
        rsi_entry_threshold=45.0,
        rsi_max_threshold=100.0,
        rsi_exit_threshold=40.0,
        volume_ma_period=5,
        volume_multiplier=0.5,
    )
    signals_df = strategy.generate_all_signals(df, "TCS.NS")
    signals = signals_df["signal"].tolist()

    assert "BUY" in signals, "Bullish crossover must produce at least one BUY signal"
    assert "SELL" in signals, "Bearish reversal must produce at least one SELL signal"

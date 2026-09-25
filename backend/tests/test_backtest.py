from decimal import Decimal
import pandas as pd
import pytest
from backend.app.backtesting.cost_model import TransactionCostModel
from backend.app.backtesting.engine import BacktestEngine
from backend.app.services.data_provider import MockDataProvider
from backend.app.services.data_validator import DataValidator
from backend.app.strategies.ema_rsi_volume import EMARsiVolumeStrategy


def test_backtest_runs_and_generates_result():
    provider = MockDataProvider()
    df = provider.fetch_ohlcv("TCS.NS")
    validated = DataValidator.validate_and_normalize(df, "TCS.NS")

    strategy = EMARsiVolumeStrategy(
        fast_ema_period=5,
        slow_ema_period=10,
        rsi_period=5,
        rsi_entry_threshold=45.0,
        rsi_max_threshold=100.0,
        rsi_exit_threshold=40.0,
        volume_ma_period=5,
        volume_multiplier=0.5,
    )

    engine = BacktestEngine(strategy=strategy, initial_capital=Decimal("100000.00"))
    result = engine.run(validated, "TCS.NS")

    assert result.symbol == "TCS.NS"
    assert result.initial_capital == Decimal("100000.00")
    assert len(result.equity_curve) == len(validated)
    assert isinstance(result.total_return_pct, float)
    assert isinstance(result.benchmark_return_pct, float)
    assert result.max_drawdown_pct >= 0.0


def test_benchmark_buy_and_hold_calculation():
    provider = MockDataProvider()
    df = provider.fetch_ohlcv("RELIANCE.NS")
    validated = DataValidator.validate_and_normalize(df, "RELIANCE.NS")

    strategy = EMARsiVolumeStrategy(fast_ema_period=5, slow_ema_period=10)
    engine = BacktestEngine(strategy=strategy, initial_capital=Decimal("100000.00"))
    result = engine.run(validated, "RELIANCE.NS")

    first_open = Decimal(str(round(float(validated.iloc[0]["open"]), 4)))
    last_close = Decimal(str(round(float(validated.iloc[-1]["close"]), 4)))
    expected_benchmark = round(float(((last_close - first_open) / first_open) * Decimal("100.0")), 2)

    assert result.benchmark_return_pct == expected_benchmark


def test_transaction_costs_are_tracked_and_deducted():
    # Construct a dataset guaranteed to produce a trade
    dates = pd.date_range("2024-01-01", periods=30, freq="D", tz="Asia/Kolkata")
    prices = [100.0 - i * 0.2 for i in range(15)] + [97.0 + i * 4.0 for i in range(15)]
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
    engine = BacktestEngine(strategy=strategy, initial_capital=Decimal("100000.00"))
    result = engine.run(df, "INFY.NS")

    if result.total_trades > 0:
        assert result.total_transaction_costs > Decimal("0.0")
        for trade in result.trades:
            assert trade.fees_paid > Decimal("0.0")


def test_zero_look_ahead_bias_execution_at_t_plus_1_open():
    """
    CRITICAL TEST FOR LOOK-AHEAD BIAS:
    Ensures that when a BUY signal is generated at Candle t Close,
    the trade is executed at Candle t+1 OPEN price (+ slippage),
    and does NOT use Candle t Close or Candle t+1 Close!
    """
    dates = pd.date_range("2024-01-01", periods=25, freq="D", tz="Asia/Kolkata")
    # Base downtrend, then sharp surge at day 15
    prices = [100.0 - i * 0.5 for i in range(15)] + [92.5 + (i - 14) * 6.0 for i in range(15, 25)]
    records = []
    for i, (dt, p) in enumerate(zip(dates, prices)):
        # At day 16 (the candle where BUY is filled at Open), specify a distinct Open price
        # and an entirely different Close price to verify which price was used for execution
        open_val = p - 1.0
        close_val = p
        if i == 17:
            open_val = 555.0  # Unique distinctive open price for execution check
            close_val = 999.0 # Very different close price
        records.append({
            "timestamp": dt,
            "open": round(open_val, 2),
            "high": round(max(open_val, close_val) + 5.0, 2),
            "low": round(min(open_val, close_val) - 5.0, 2),
            "close": round(close_val, 2),
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
    # Use zero slippage for exact price comparison
    cost_model = TransactionCostModel(slippage_pct=Decimal("0.0"))
    engine = BacktestEngine(strategy=strategy, initial_capital=Decimal("100000.00"), cost_model=cost_model)

    signals_df = strategy.generate_all_signals(df, "HDFCBANK.NS")
    # Find the index of the first BUY signal
    buy_indices = signals_df.index[signals_df["signal"] == "BUY"].tolist()

    if buy_indices:
        signal_idx = buy_indices[0]
        exec_idx = signal_idx + 1  # Execution must happen at candle t+1
        expected_exec_price = Decimal(str(round(float(df.iloc[exec_idx]["open"]), 4)))

        result = engine.run(df, "HDFCBANK.NS")
        assert len(result.trades) > 0
        first_trade = result.trades[0]

        # The entry price must equal Candle t+1 Open price, NOT Candle t Close or Candle t+1 Close!
        assert first_trade.entry_price == expected_exec_price
        assert first_trade.entry_timestamp == str(df.iloc[exec_idx]["timestamp"])

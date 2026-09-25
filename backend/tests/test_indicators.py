import pytest
import numpy as np
import pandas as pd
from backend.app.services.indicator_service import IndicatorService


def test_ema_mathematical_precision():
    """
    Tests that calculate_ema precisely follows:
    alpha = 2 / (period + 1)
    EMA_t = alpha * Close_t + (1 - alpha) * EMA_(t-1)
    """
    period = 3
    alpha = 2.0 / (period + 1)  # 2 / 4 = 0.5
    prices = pd.Series([10.0, 20.0, 30.0, 40.0, 50.0])

    # Manual analytical calculation:
    # t=0: 10.0
    # t=1: 0.5 * 20.0 + 0.5 * 10.0 = 15.0
    # t=2: 0.5 * 30.0 + 0.5 * 15.0 = 22.5
    # t=3: 0.5 * 40.0 + 0.5 * 22.5 = 31.25
    # t=4: 0.5 * 50.0 + 0.5 * 31.25 = 40.625
    expected = [10.0, 15.0, 22.5, 31.25, 40.625]

    result = IndicatorService.calculate_ema(prices, period=period)
    np.testing.assert_allclose(result.values, expected, rtol=1e-5)


def test_rsi_bounded_between_zero_and_hundred():
    """
    Verifies that RSI is strictly bounded in [0, 100].
    """
    # Create an oscillating series of 100 points
    np.random.seed(42)
    prices = pd.Series(100.0 + np.cumsum(np.random.randn(100)))
    rsi = IndicatorService.calculate_rsi(prices, period=14)

    valid_rsi = rsi.dropna()
    assert (valid_rsi >= 0.0).all()
    assert (valid_rsi <= 100.0).all()


def test_rsi_all_gains_reaches_hundred():
    """
    When prices only increase monotonically, RSI must reach 100.
    """
    prices = pd.Series([float(i * 10) for i in range(1, 30)])
    rsi = IndicatorService.calculate_rsi(prices, period=14)
    valid_rsi = rsi.dropna()
    assert np.isclose(valid_rsi.iloc[-1], 100.0)


def test_rsi_all_losses_reaches_zero():
    """
    When prices only decrease monotonically, RSI must reach 0.
    """
    prices = pd.Series([float(1000 - i * 10) for i in range(1, 30)])
    rsi = IndicatorService.calculate_rsi(prices, period=14)
    valid_rsi = rsi.dropna()
    assert np.isclose(valid_rsi.iloc[-1], 0.0)


def test_volume_ma_calculation():
    volumes = pd.Series([100.0] * 20 + [200.0] * 5)
    vma = IndicatorService.calculate_volume_ma(volumes, period=20)
    # First 19 values should be NaN
    assert vma.iloc[:19].isna().all()
    # 20th value should be 100.0
    assert vma.iloc[19] == 100.0

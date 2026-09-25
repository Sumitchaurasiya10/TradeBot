from typing import Any, Dict, Optional
import numpy as np
import pandas as pd
from backend.app.services.indicator_service import IndicatorService
from backend.app.strategies.base import BaseStrategy, SignalType, StrategySignal


class EMARsiVolumeStrategy(BaseStrategy):
    """
    Rule-based strategy combining:
    1. Fast EMA / Slow EMA Crossover (Trend direction)
    2. RSI (Momentum confirmation, bounded 0-100)
    3. Volume MA Confirmation (Breakout volume validity)

    All parameters are fully configurable.
    """

    def __init__(
        self,
        fast_ema_period: int = 9,
        slow_ema_period: int = 21,
        rsi_period: int = 14,
        rsi_entry_threshold: float = 50.0,
        rsi_max_threshold: float = 85.0,
        rsi_exit_threshold: float = 45.0,
        volume_ma_period: int = 20,
        volume_multiplier: float = 1.0,
        stop_loss_pct: float = 0.02,
        take_profit_pct: float = 0.05,
    ):
        if fast_ema_period >= slow_ema_period:
            raise ValueError(
                f"fast_ema_period ({fast_ema_period}) must be strictly less than slow_ema_period ({slow_ema_period})"
            )

        self.fast_ema_period = fast_ema_period
        self.slow_ema_period = slow_ema_period
        self.rsi_period = rsi_period
        self.rsi_entry_threshold = rsi_entry_threshold
        self.rsi_max_threshold = rsi_max_threshold
        self.rsi_exit_threshold = rsi_exit_threshold
        self.volume_ma_period = volume_ma_period
        self.volume_multiplier = volume_multiplier
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct

    def get_parameters(self) -> Dict[str, Any]:
        return {
            "fast_ema_period": self.fast_ema_period,
            "slow_ema_period": self.slow_ema_period,
            "rsi_period": self.rsi_period,
            "rsi_entry_threshold": self.rsi_entry_threshold,
            "rsi_max_threshold": self.rsi_max_threshold,
            "rsi_exit_threshold": self.rsi_exit_threshold,
            "volume_ma_period": self.volume_ma_period,
            "volume_multiplier": self.volume_multiplier,
            "stop_loss_pct": self.stop_loss_pct,
            "take_profit_pct": self.take_profit_pct,
        }

    def _prepare_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        return IndicatorService.enrich_dataframe(
            df=df,
            fast_ema_period=self.fast_ema_period,
            slow_ema_period=self.slow_ema_period,
            rsi_period=self.rsi_period,
            volume_ma_period=self.volume_ma_period,
        )

    def generate_signal(self, df: pd.DataFrame, symbol: str) -> StrategySignal:
        if df is None or len(df) < self.slow_ema_period + 2:
            return StrategySignal(
                signal=SignalType.HOLD,
                timestamp=str(df["timestamp"].iloc[-1]) if df is not None and not df.empty else "",
                symbol=symbol,
                reason="Insufficient historical bars for indicator calculation",
                indicators={},
            )

        enriched = self._prepare_indicators(df)
        curr = enriched.iloc[-1]
        prev = enriched.iloc[-2]

        fast_curr = curr[f"ema_{self.fast_ema_period}"]
        slow_curr = curr[f"ema_{self.slow_ema_period}"]
        fast_prev = prev[f"ema_{self.fast_ema_period}"]
        slow_prev = prev[f"ema_{self.slow_ema_period}"]

        rsi_curr = curr[f"rsi_{self.rsi_period}"]
        vol_curr = curr["volume"]
        vol_ma_curr = curr[f"volume_ma_{self.volume_ma_period}"]

        indicator_payload = {
            "fast_ema": round(float(fast_curr), 2) if not pd.isna(fast_curr) else None,
            "slow_ema": round(float(slow_curr), 2) if not pd.isna(slow_curr) else None,
            "rsi": round(float(rsi_curr), 2) if not pd.isna(rsi_curr) else None,
            "volume": int(vol_curr) if not pd.isna(vol_curr) else None,
            "volume_ma": round(float(vol_ma_curr), 2) if not pd.isna(vol_ma_curr) else None,
            "close": round(float(curr["close"]), 2),
        }

        # Check for warm-up NaN values
        if pd.isna(fast_curr) or pd.isna(slow_curr) or pd.isna(rsi_curr) or pd.isna(vol_ma_curr):
            return StrategySignal(
                signal=SignalType.HOLD,
                timestamp=str(curr["timestamp"]),
                symbol=symbol,
                reason="Indicators warming up",
                indicators=indicator_payload,
            )

        # 1. Bullish condition: Fast EMA crosses above Slow EMA
        is_bullish_cross = (fast_prev <= slow_prev) and (fast_curr > slow_curr)
        # Momentum condition: RSI between entry threshold and max threshold
        is_rsi_bullish = (rsi_curr >= self.rsi_entry_threshold) and (rsi_curr <= self.rsi_max_threshold)
        # Volume condition: current volume meets threshold
        is_volume_confirmed = vol_curr >= (vol_ma_curr * self.volume_multiplier)

        # 2. Bearish condition: Fast EMA crosses below Slow EMA OR RSI drops below exit threshold
        is_bearish_cross = (fast_prev >= slow_prev) and (fast_curr < slow_curr)
        is_rsi_bearish = rsi_curr <= self.rsi_exit_threshold

        if is_bullish_cross and is_rsi_bullish and is_volume_confirmed:
            return StrategySignal(
                signal=SignalType.BUY,
                timestamp=str(curr["timestamp"]),
                symbol=symbol,
                reason=(
                    f"Bullish EMA crossover ({fast_curr:.2f} > {slow_curr:.2f}) "
                    f"with RSI {rsi_curr:.2f} (threshold: {self.rsi_entry_threshold}) "
                    f"and Volume confirmation ({vol_curr} >= {vol_ma_curr * self.volume_multiplier:.0f})"
                ),
                indicators=indicator_payload,
            )

        if is_bearish_cross or is_rsi_bearish:
            reasons = []
            if is_bearish_cross:
                reasons.append(f"Bearish EMA crossover ({fast_curr:.2f} < {slow_curr:.2f})")
            if is_rsi_bearish:
                reasons.append(f"RSI {rsi_curr:.2f} <= {self.rsi_exit_threshold}")
            return StrategySignal(
                signal=SignalType.SELL,
                timestamp=str(curr["timestamp"]),
                symbol=symbol,
                reason=" and ".join(reasons),
                indicators=indicator_payload,
            )

        return StrategySignal(
            signal=SignalType.HOLD,
            timestamp=str(curr["timestamp"]),
            symbol=symbol,
            reason="Market neutral: No crossover or threshold trigger",
            indicators=indicator_payload,
        )

    def generate_all_signals(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """
        Calculates signals across the historical series.
        Appends 'signal' column with 'BUY', 'SELL', 'HOLD'.
        """
        enriched = self._prepare_indicators(df)
        signals = [SignalType.HOLD.value] * len(enriched)

        fast_col = f"ema_{self.fast_ema_period}"
        slow_col = f"ema_{self.slow_ema_period}"
        rsi_col = f"rsi_{self.rsi_period}"
        vol_ma_col = f"volume_ma_{self.volume_ma_period}"

        for i in range(1, len(enriched)):
            curr = enriched.iloc[i]
            prev = enriched.iloc[i - 1]

            fast_curr, slow_curr = curr[fast_col], curr[slow_col]
            fast_prev, slow_prev = prev[fast_col], prev[slow_col]
            rsi_curr = curr[rsi_col]
            vol_curr = curr["volume"]
            vol_ma_curr = curr[vol_ma_col]

            if pd.isna(fast_curr) or pd.isna(slow_curr) or pd.isna(rsi_curr) or pd.isna(vol_ma_curr):
                continue

            is_bullish_cross = (fast_prev <= slow_prev) and (fast_curr > slow_curr)
            is_rsi_bullish = (rsi_curr >= self.rsi_entry_threshold) and (rsi_curr <= self.rsi_max_threshold)
            is_volume_confirmed = vol_curr >= (vol_ma_curr * self.volume_multiplier)

            is_bearish_cross = (fast_prev >= slow_prev) and (fast_curr < slow_curr)
            is_rsi_bearish = rsi_curr <= self.rsi_exit_threshold

            if is_bullish_cross and is_rsi_bullish and is_volume_confirmed:
                signals[i] = SignalType.BUY.value
            elif is_bearish_cross or is_rsi_bearish:
                signals[i] = SignalType.SELL.value

        enriched["signal"] = signals
        return enriched

from datetime import datetime
from decimal import Decimal
from typing import Optional
import pandas as pd
import pytz

from backend.app.schemas.strategy import SignalResponse
from backend.app.services.market_data.base import MarketDataProvider
from backend.app.strategies.ema_rsi_volume import EMARsiVolumeStrategy

IST = pytz.timezone("Asia/Kolkata")


class LiveStrategyEvaluator:
    """
    Evaluates real-time / streaming market data against the rule-based
    EMA + RSI + Volume Confirmation strategy without look-ahead bias.
    """

    @classmethod
    async def evaluate_live_signal(
        cls,
        symbol: str,
        provider: MarketDataProvider,
        fast_ema: int = 9,
        slow_ema: int = 21,
        rsi_period: int = 14,
        volume_ma_period: int = 20,
        rsi_entry_threshold: float = 50.0,
        rsi_max_threshold: float = 85.0,
        rsi_exit_threshold: float = 45.0,
        volume_multiplier: float = 1.0,
    ) -> SignalResponse:
        clean = symbol.upper().replace(".NS", "").replace(".BO", "").strip()

        # 1. Fetch historical bars for baseline indicators
        hist_df = await provider.get_historical_data(clean)

        # 2. Fetch latest live quote
        live_quote = await provider.get_quote(clean)

        # 3. If we have historical bars, append or update with current live quote
        if hist_df is not None and not hist_df.empty:
            df = hist_df.copy()
            # If live quote is newer than last historical bar, append as current candle
            last_ts = pd.to_datetime(df["timestamp"].iloc[-1])
            quote_ts = live_quote.timestamp

            # Create current bar record
            current_bar = {
                "timestamp": quote_ts,
                "open": float(live_quote.open or live_quote.last_price),
                "high": float(live_quote.high or live_quote.last_price),
                "low": float(live_quote.low or live_quote.last_price),
                "close": float(live_quote.last_price),
                "volume": int(live_quote.volume),
            }

            # Check if last bar has same date
            if hasattr(last_ts, "date") and hasattr(quote_ts, "date") and last_ts.date() == quote_ts.date():
                df.iloc[-1] = current_bar
            else:
                df = pd.concat([df, pd.DataFrame([current_bar])], ignore_index=True)
        else:
            # Fallback if historical data is unavailable
            df = pd.DataFrame([{
                "timestamp": live_quote.timestamp,
                "open": float(live_quote.open or live_quote.last_price),
                "high": float(live_quote.high or live_quote.last_price),
                "low": float(live_quote.low or live_quote.last_price),
                "close": float(live_quote.last_price),
                "volume": int(live_quote.volume),
            }])

        strategy = EMARsiVolumeStrategy(
            fast_ema_period=fast_ema,
            slow_ema_period=slow_ema,
            rsi_period=rsi_period,
            rsi_entry_threshold=rsi_entry_threshold,
            rsi_max_threshold=rsi_max_threshold,
            rsi_exit_threshold=rsi_exit_threshold,
            volume_ma_period=volume_ma_period,
            volume_multiplier=volume_multiplier,
        )

        signal_obj = strategy.generate_signal(df, clean)

        return SignalResponse(
            signal=signal_obj.signal.value,
            timestamp=signal_obj.timestamp,
            symbol=signal_obj.symbol,
            reason=signal_obj.reason,
            indicators=signal_obj.indicators,
            parameters=strategy.get_parameters(),
        )
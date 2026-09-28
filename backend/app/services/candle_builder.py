from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Dict, List, Optional
import pandas as pd
import pytz

IST = pytz.timezone("Asia/Kolkata")


class LiveCandle:
    def __init__(self, symbol: str, timeframe_minutes: int, bucket_start: datetime, first_price: Decimal, first_vol: int):
        self.symbol = symbol
        self.timeframe_minutes = timeframe_minutes
        self.bucket_start = bucket_start
        self.open = first_price
        self.high = first_price
        self.low = first_price
        self.close = first_price
        self.volume = first_vol
        self.tick_count = 1

    def update(self, price: Decimal, volume_delta: int):
        if price > self.high:
            self.high = price
        if price < self.low:
            self.low = price
        self.close = price
        self.volume += volume_delta
        self.tick_count += 1

    def to_dict(self) -> dict:
        return {
            "timestamp": self.bucket_start,
            "open": float(self.open),
            "high": float(self.high),
            "low": float(self.low),
            "close": float(self.close),
            "volume": int(self.volume),
        }


class CandleAggregator:
    """
    Aggregates live price ticks into timeframe candles (1m, 5m, 15m, 1D).
    Timezone-aware with 'Asia/Kolkata' bucket alignment.
    """

    SUPPORTED_TIMEFRAMES = {
        "1m": 1,
        "5m": 5,
        "15m": 15,
        "1D": 1440,
    }

    def __init__(self, max_history_bars: int = 500):
        self.max_history_bars = max_history_bars
        # Map: (symbol, tf) -> LiveCandle
        self._current_candles: Dict[str, LiveCandle] = {}
        # Map: (symbol, tf) -> List[dict]
        self._completed_bars: Dict[str, List[dict]] = {}

    def _normalize_symbol(self, symbol: str) -> str:
        return symbol.upper().replace(".NS", "").replace(".BO", "").strip()

    def _get_bucket_start(self, dt: datetime, tf_minutes: int) -> datetime:
        if dt.tzinfo is None:
            dt = IST.localize(dt)
        else:
            dt = dt.astimezone(IST)

        if tf_minutes == 1440:
            # 1D bucket starts at 00:00:00 IST
            return dt.replace(hour=0, minute=0, second=0, microsecond=0)

        # Minute buckets aligned from top of the hour
        minute_bucket = (dt.minute // tf_minutes) * tf_minutes
        return dt.replace(minute=minute_bucket, second=0, microsecond=0)

    def add_tick(
        self,
        symbol: str,
        price: Decimal,
        volume: int = 0,
        timestamp: Optional[datetime] = None,
        timeframe: str = "1m",
    ) -> Optional[dict]:
        """
        Processes a single incoming tick.
        If a candle completes (rolls over to next bucket), returns the completed candle dict.
        """
        clean = self._normalize_symbol(symbol)
        tf_mins = self.SUPPORTED_TIMEFRAMES.get(timeframe, 1)
        key = f"{clean}:{timeframe}"

        ts = timestamp or datetime.now(IST)
        bucket_start = self._get_bucket_start(ts, tf_mins)

        active = self._current_candles.get(key)
        completed_candle_dict = None

        if active is None:
            self._current_candles[key] = LiveCandle(clean, tf_mins, bucket_start, price, volume)
        elif active.bucket_start != bucket_start:
            # Bucket has rolled over! Finalize active candle
            completed_candle_dict = active.to_dict()
            if key not in self._completed_bars:
                self._completed_bars[key] = []
            self._completed_bars[key].append(completed_candle_dict)

            # Cap history
            if len(self._completed_bars[key]) > self.max_history_bars:
                self._completed_bars[key] = self._completed_bars[key][-self.max_history_bars:]

            # Start new candle
            self._current_candles[key] = LiveCandle(clean, tf_mins, bucket_start, price, volume)
        else:
            # Update existing active candle
            active.update(price, volume)

        return completed_candle_dict

    def get_current_candle(self, symbol: str, timeframe: str = "1m") -> Optional[dict]:
        clean = self._normalize_symbol(symbol)
        key = f"{clean}:{timeframe}"
        active = self._current_candles.get(key)
        return active.to_dict() if active else None

    def get_bars_dataframe(self, symbol: str, timeframe: str = "1m", include_current: bool = True) -> pd.DataFrame:
        clean = self._normalize_symbol(symbol)
        key = f"{clean}:{timeframe}"
        bars = list(self._completed_bars.get(key, []))

        if include_current:
            curr = self.get_current_candle(symbol, timeframe)
            if curr:
                bars.append(curr)

        if not bars:
            return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])

        df = pd.DataFrame(bars)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        return df


# Global singleton candle aggregator
candle_aggregator = CandleAggregator()
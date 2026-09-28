from datetime import datetime, timedelta
from decimal import Decimal
import json
import pytest
import pytz
from starlette.testclient import TestClient

from backend.app.main import app
from backend.app.services.candle_builder import CandleAggregator
from backend.app.services.market_data import reset_market_data_provider
from backend.app.services.market_data.mock_provider import MockLiveMarketDataProvider

IST = pytz.timezone("Asia/Kolkata")


def test_candle_aggregator_intra_bucket_updates():
    agg = CandleAggregator()
    t0 = IST.localize(datetime(2026, 9, 30, 9, 15, 10))

    # First tick
    agg.add_tick("TCS", Decimal("3500.00"), volume=100, timestamp=t0, timeframe="1m")
    candle = agg.get_current_candle("TCS", "1m")
    assert candle is not None
    assert candle["open"] == 3500.00
    assert candle["high"] == 3500.00
    assert candle["low"] == 3500.00
    assert candle["close"] == 3500.00
    assert candle["volume"] == 100

    # Second tick: higher price
    t1 = t0 + timedelta(seconds=15)
    agg.add_tick("TCS", Decimal("3510.50"), volume=50, timestamp=t1, timeframe="1m")

    # Third tick: lower price
    t2 = t0 + timedelta(seconds=35)
    agg.add_tick("TCS", Decimal("3495.00"), volume=75, timestamp=t2, timeframe="1m")

    candle = agg.get_current_candle("TCS", "1m")
    assert candle["open"] == 3500.00
    assert candle["high"] == 3510.50
    assert candle["low"] == 3495.00
    assert candle["close"] == 3495.00
    assert candle["volume"] == 225


def test_candle_aggregator_bucket_rollover():
    agg = CandleAggregator()
    t0 = IST.localize(datetime(2026, 9, 30, 9, 15, 20))
    agg.add_tick("RELIANCE", Decimal("1300.00"), volume=500, timestamp=t0, timeframe="1m")

    # Roll over to 09:16:05 (next minute bucket)
    t_next = IST.localize(datetime(2026, 9, 30, 9, 16, 5))
    completed = agg.add_tick("RELIANCE", Decimal("1305.00"), volume=300, timestamp=t_next, timeframe="1m")

    assert completed is not None
    assert completed["close"] == 1300.00
    assert completed["volume"] == 500

    df = agg.get_bars_dataframe("RELIANCE", "1m", include_current=True)
    assert len(df) == 2
    assert "timestamp" in df.columns
    assert "close" in df.columns


def test_websocket_market_feed_connection_and_ping():
    reset_market_data_provider(MockLiveMarketDataProvider())
    client = TestClient(app)

    with client.websocket_connect("/api/v1/ws/market") as ws:
        # Send ping
        ws.send_text(json.dumps({"action": "ping"}))

        # Receive messages until we get pong or stream update
        received_types = set()
        for _ in range(5):
            msg_text = ws.receive_text()
            data = json.loads(msg_text)
            received_types.add(data.get("type"))
            if "pong" in received_types:
                break

        assert "pong" in received_types or "market_status" in received_types
    reset_market_data_provider()
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import math
from typing import Dict, List, Optional
import numpy as np
import pandas as pd
import pytz

from backend.app.schemas.market import (
    AssetType,
    DataStatus,
    FNOQuote,
    IndexQuote,
    InstrumentType,
    OptionChainResponse,
    OptionChainStrikeRow,
    OptionType,
    Quote,
)
from backend.app.services.market_data.base import MarketDataProvider

IST = pytz.timezone("Asia/Kolkata")


class MockLiveMarketDataProvider(MarketDataProvider):
    """
    High-fidelity deterministic simulated market data provider.
    Provides realistic quotes, indices, and full F&O option chains for offline testing,
    weekend development, and automated test suites.
    All data is clearly labeled as DataStatus.DEMO_DATA.
    """

    BASE_EQUITIES: Dict[str, Dict] = {
        "RELIANCE": {"price": 1285.50, "prev_close": 1272.00, "open": 1275.00, "high": 1292.00, "low": 1270.00, "vol": 7820000},
        "TCS": {"price": 3120.00, "prev_close": 3095.50, "open": 3100.00, "high": 3135.00, "low": 3085.00, "vol": 2150000},
        "INFY": {"price": 1495.20, "prev_close": 1510.00, "open": 1508.00, "high": 1515.00, "low": 1490.00, "vol": 5400000},
        "HDFCBANK": {"price": 1640.00, "prev_close": 1630.00, "open": 1632.00, "high": 1648.00, "low": 1625.00, "vol": 12400000},
        "ICICIBANK": {"price": 1225.75, "prev_close": 1215.00, "open": 1218.00, "high": 1232.00, "low": 1212.00, "vol": 8900000},
        "SBIN": {"price": 815.40, "prev_close": 820.00, "open": 822.00, "high": 825.00, "low": 810.00, "vol": 9500000},
        "ITC": {"price": 465.30, "prev_close": 462.10, "open": 463.00, "high": 468.00, "low": 461.50, "vol": 6200000},
        "LT": {"price": 3680.00, "prev_close": 3640.00, "open": 3650.00, "high": 3695.00, "low": 3635.00, "vol": 1100000},
    }

    BASE_INDICES: Dict[str, Dict] = {
        "NIFTY 50": {"price": 25150.00, "prev_close": 25020.00, "open": 25060.00, "high": 25210.00, "low": 25040.00, "exchange": "NSE"},
        "SENSEX": {"price": 82400.00, "prev_close": 81980.00, "open": 82100.00, "high": 82600.00, "low": 82050.00, "exchange": "BSE"},
        "BANK NIFTY": {"price": 53200.00, "prev_close": 52950.00, "open": 53020.00, "high": 53380.00, "low": 52980.00, "exchange": "NSE"},
    }

    def __init__(self, tick_seed: int = 42, default_status: DataStatus = DataStatus.DEMO_DATA):
        self._seed = tick_seed
        self._counter = 0
        self._status = default_status

    def get_provider_name(self) -> str:
        return "mock"

    def _now(self) -> datetime:
        return datetime.now(IST)

    def _clean_symbol(self, symbol: str) -> str:
        return symbol.upper().replace(".NS", "").replace(".BO", "").strip()

    async def get_quote(self, symbol: str) -> Quote:
        clean = self._clean_symbol(symbol)
        data = self.BASE_EQUITIES.get(clean)
        now = self._now()

        if not data:
            # Fallback for arbitrary symbols
            data = {"price": 1000.00, "prev_close": 1000.00, "open": 1000.00, "high": 1010.00, "low": 990.00, "vol": 500000}

        price = Decimal(str(data["price"]))
        prev_close = Decimal(str(data["prev_close"]))
        open_p = Decimal(str(data["open"]))
        high_p = Decimal(str(data["high"]))
        low_p = Decimal(str(data["low"]))
        change = price - prev_close
        pct = (change / prev_close) * Decimal("100.0") if prev_close else Decimal("0.0")

        return Quote(
            symbol=clean,
            exchange="NSE",
            asset_type=AssetType.EQUITY,
            timestamp=now,
            last_price=price,
            open=open_p,
            high=high_p,
            low=low_p,
            previous_close=prev_close,
            change=round(change, 2),
            change_percent=round(pct, 2),
            volume=data["vol"],
            bid_price=price - Decimal("0.05"),
            ask_price=price + Decimal("0.05"),
            bid_quantity=1500,
            ask_quantity=1200,
            data_status=self._status,
        )

    async def get_quotes(self, symbols: List[str]) -> List[Quote]:
        return [await self.get_quote(s) for s in symbols]

    async def get_index_quote(self, symbol: str) -> IndexQuote:
        norm = symbol.upper().strip()
        data = self.BASE_INDICES.get(norm)
        now = self._now()

        if not data:
            if "NIFTY" in norm and "BANK" not in norm:
                data = self.BASE_INDICES["NIFTY 50"]
            elif "BANK" in norm:
                data = self.BASE_INDICES["BANK NIFTY"]
            elif "SENSEX" in norm:
                data = self.BASE_INDICES["SENSEX"]
            else:
                data = {"price": 20000.0, "prev_close": 20000.0, "open": 20000.0, "high": 20100.0, "low": 19900.0, "exchange": "NSE"}

        price = Decimal(str(data["price"]))
        prev_close = Decimal(str(data["prev_close"]))
        open_p = Decimal(str(data["open"]))
        high_p = Decimal(str(data["high"]))
        low_p = Decimal(str(data["low"]))
        change = price - prev_close
        pct = (change / prev_close) * Decimal("100.0") if prev_close else Decimal("0.0")

        return IndexQuote(
            symbol=symbol,
            exchange=data.get("exchange", "NSE"),
            timestamp=now,
            last_price=price,
            open=open_p,
            high=high_p,
            low=low_p,
            previous_close=prev_close,
            change=round(change, 2),
            change_percent=round(pct, 2),
            data_status=self._status,
        )

    async def get_indices_quotes(self) -> List[IndexQuote]:
        return [
            await self.get_index_quote("NIFTY 50"),
            await self.get_index_quote("SENSEX"),
            await self.get_index_quote("BANK NIFTY"),
        ]

    async def get_fno_contracts(self, underlying: str) -> List[FNOQuote]:
        clean = self._clean_symbol(underlying)
        # Fetch option chain and flatten
        chain = await self.get_option_chain(clean)
        contracts: List[FNOQuote] = []
        for strike_row in chain.strikes:
            if strike_row.call:
                contracts.append(strike_row.call)
            if strike_row.put:
                contracts.append(strike_row.put)
        return contracts

    async def get_option_chain(
        self, underlying: str, expiry: Optional[str] = None
    ) -> OptionChainResponse:
        clean = self._clean_symbol(underlying)
        now = self._now()

        # Determine spot price
        if clean in ["NIFTY", "NIFTY 50"]:
            spot = Decimal("25150.00")
            strike_step = Decimal("50.00")
            num_strikes = 10
        elif clean in ["BANKNIFTY", "BANK NIFTY"]:
            spot = Decimal("53200.00")
            strike_step = Decimal("100.00")
            num_strikes = 10
        else:
            eq = await self.get_quote(clean)
            spot = eq.last_price
            strike_step = Decimal("20.00") if spot > 1000 else Decimal("10.00")
            num_strikes = 7

        # Determine expiries: upcoming Thursdays
        expiries = []
        curr = now
        while len(expiries) < 4:
            # Thursday is weekday 3
            days_ahead = (3 - curr.weekday()) % 7
            if days_ahead == 0 and curr.hour >= 15 and curr.minute >= 30:
                days_ahead = 7
            target = curr + timedelta(days=days_ahead if days_ahead > 0 else 7)
            exp_str = target.strftime("%Y-%m-%d")
            if exp_str not in expiries:
                expiries.append(exp_str)
            curr = target + timedelta(days=1)

        selected_expiry = expiry if expiry and expiry in expiries else expiries[0]

        # ATM Strike rounded to step
        atm_strike = (round(spot / strike_step)) * strike_step

        strikes_list: List[OptionChainStrikeRow] = []
        for i in range(-num_strikes, num_strikes + 1):
            k = atm_strike + (Decimal(str(i)) * strike_step)
            diff = spot - k

            # Approximate realistic Black-Scholes-like option price
            base_vol = Decimal("0.15")  # 15% IV
            intrinsic_ce = max(Decimal("0.0"), diff)
            time_val_ce = max(Decimal("10.0"), Decimal("120.0") - (abs(diff) * Decimal("0.12")))
            call_ltp = round(intrinsic_ce + time_val_ce, 2)

            intrinsic_pe = max(Decimal("0.0"), -diff)
            time_val_pe = max(Decimal("10.0"), Decimal("120.0") - (abs(diff) * Decimal("0.12")))
            put_ltp = round(intrinsic_pe + time_val_pe, 2)

            # Realistic Open Interest (highest near ATM)
            oi_factor = max(1, 100 - (abs(i) * 8))
            call_oi = int(150000 * (oi_factor / 100.0))
            put_oi = int(140000 * (oi_factor / 100.0))

            call_quote = FNOQuote(
                underlying=clean,
                symbol=f"{clean}{selected_expiry.replace('-', '')}{int(k)}CE",
                exchange="NSE",
                instrument_type=InstrumentType.OPTIDX if "NIFTY" in clean else InstrumentType.OPTSTK,
                expiry=selected_expiry,
                strike_price=k,
                option_type=OptionType.CE,
                timestamp=now,
                last_price=call_ltp,
                change=Decimal("5.25") if i < 0 else Decimal("-4.10"),
                change_percent=Decimal("3.85") if i < 0 else Decimal("-3.15"),
                volume=int(call_oi * 0.4),
                open_interest=call_oi,
                change_in_oi=int(call_oi * 0.05),
                bid_price=call_ltp - Decimal("0.50"),
                ask_price=call_ltp + Decimal("0.50"),
                bid_quantity=1800,
                ask_quantity=1500,
                implied_volatility=Decimal("14.50"),
                data_status=self._status,
            )

            put_quote = FNOQuote(
                underlying=clean,
                symbol=f"{clean}{selected_expiry.replace('-', '')}{int(k)}PE",
                exchange="NSE",
                instrument_type=InstrumentType.OPTIDX if "NIFTY" in clean else InstrumentType.OPTSTK,
                expiry=selected_expiry,
                strike_price=k,
                option_type=OptionType.PE,
                timestamp=now,
                last_price=put_ltp,
                change=Decimal("-3.40") if i < 0 else Decimal("6.10"),
                change_percent=Decimal("-2.50") if i < 0 else Decimal("4.20"),
                volume=int(put_oi * 0.4),
                open_interest=put_oi,
                change_in_oi=int(put_oi * 0.04),
                bid_price=put_ltp - Decimal("0.50"),
                ask_price=put_ltp + Decimal("0.50"),
                bid_quantity=1600,
                ask_quantity=1400,
                implied_volatility=Decimal("15.20"),
                data_status=self._status,
            )

            strikes_list.append(OptionChainStrikeRow(strike_price=k, call=call_quote, put=put_quote))

        return OptionChainResponse(
            underlying=clean,
            underlying_price=spot,
            expiry=selected_expiry,
            available_expiries=expiries,
            timestamp=now,
            data_status=self._status,
            strikes=strikes_list,
        )

    async def get_historical_data(
        self,
        symbol: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        interval: str = "1d",
    ) -> pd.DataFrame:
        clean = self._clean_symbol(symbol)
        base = self.BASE_EQUITIES.get(clean, {"price": 1000.0})["price"]

        dates = pd.date_range(start="2024-01-01", periods=100, freq="D", tz="Asia/Kolkata")
        records = []
        curr = base

        for i, dt in enumerate(dates):
            change = (i % 5 - 2) * 4.0
            curr = max(100.0, curr + change)
            open_p = curr - 2.0
            high_p = curr + 6.0
            low_p = curr - 5.0
            close_p = curr
            records.append({
                "timestamp": dt,
                "open": round(open_p, 2),
                "high": round(high_p, 2),
                "low": round(low_p, 2),
                "close": round(close_p, 2),
                "volume": 1000000 + (i * 15000),
            })

        return pd.DataFrame(records)
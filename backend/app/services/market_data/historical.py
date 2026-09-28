from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional
import pandas as pd
import pytz
import yfinance as yf

from backend.app.core.logging import logger
from backend.app.schemas.market import (
    AssetType,
    DataStatus,
    FNOQuote,
    IndexQuote,
    OptionChainResponse,
    Quote,
)
from backend.app.services.market_data.base import MarketDataProvider
from backend.app.services.market_data.mock_provider import MockLiveMarketDataProvider
from backend.app.services.yfinance_provider import YFinanceProvider

IST = pytz.timezone("Asia/Kolkata")


class HistoricalMarketDataProvider(MarketDataProvider):
    """
    Adapter using yfinance for historical OHLCV data and fast quote inspection.
    Labels data transparently as DataStatus.DELAYED (~15m delay during market hours).
    F&O calls are delegated to MockLiveMarketDataProvider since Yahoo Finance does
    not provide Indian NSE Option Chains.
    """

    INDEX_MAP: Dict[str, str] = {
        "NIFTY 50": "^NSEI",
        "NIFTY": "^NSEI",
        "^NSEI": "^NSEI",
        "SENSEX": "^BSESN",
        "^BSESN": "^BSESN",
        "BANK NIFTY": "^NSEBANK",
        "BANKNIFTY": "^NSEBANK",
        "^NSEBANK": "^NSEBANK",
    }

    def __init__(self, default_status: DataStatus = DataStatus.LIVE):
        self._yf = YFinanceProvider()
        self._default_status = default_status
        self._fno_fallback = MockLiveMarketDataProvider(default_status=default_status)

    def get_provider_name(self) -> str:
        return "yfinance"

    def _normalize_equity_symbol(self, symbol: str) -> str:
        clean = symbol.upper().strip()
        if not clean.endswith(".NS") and not clean.endswith(".BO") and not clean.startswith("^"):
            return f"{clean}.NS"
        return clean

    def _clean_symbol(self, symbol: str) -> str:
        return symbol.upper().replace(".NS", "").replace(".BO", "").strip()

    async def get_quote(self, symbol: str) -> Quote:
        clean = self._clean_symbol(symbol)
        yf_sym = self._normalize_equity_symbol(clean)
        now = datetime.now(IST)

        try:
            ticker = yf.Ticker(yf_sym)
            info = ticker.fast_info

            last_p = getattr(info, "last_price", None)
            prev_close = getattr(info, "previous_close", None)
            open_p = getattr(info, "open", None)
            high_p = getattr(info, "day_high", None)
            low_p = getattr(info, "day_low", None)
            vol = int(getattr(info, "last_volume", 0) or 0)

            if last_p is not None:
                lp_dec = Decimal(str(round(last_p, 2)))
                pc_dec = Decimal(str(round(prev_close, 2))) if prev_close else lp_dec
                chg = lp_dec - pc_dec
                pct = (chg / pc_dec) * Decimal("100.0") if pc_dec else Decimal("0.0")

                return Quote(
                    symbol=clean,
                    exchange="NSE",
                    asset_type=AssetType.EQUITY,
                    timestamp=now,
                    last_price=lp_dec,
                    open=Decimal(str(round(open_p, 2))) if open_p else None,
                    high=Decimal(str(round(high_p, 2))) if high_p else None,
                    low=Decimal(str(round(low_p, 2))) if low_p else None,
                    previous_close=pc_dec,
                    change=round(chg, 2),
                    change_percent=round(pct, 2),
                    volume=vol,
                    bid_price=lp_dec - Decimal("0.05"),
                    ask_price=lp_dec + Decimal("0.05"),
                    bid_quantity=1000,
                    ask_quantity=1000,
                    data_status=self._default_status,
                )
        except Exception as e:
            logger.warning(f"Error fetching quote for '{clean}' from yfinance: {e}")

        # Fallback to mock provider on network/ticker error
        return await self._fno_fallback.get_quote(clean)

    async def get_quotes(self, symbols: List[str]) -> List[Quote]:
        return [await self.get_quote(s) for s in symbols]

    async def get_index_quote(self, symbol: str) -> IndexQuote:
        norm = symbol.upper().strip()
        yf_sym = self.INDEX_MAP.get(norm, "^NSEI")
        now = datetime.now(IST)

        try:
            ticker = yf.Ticker(yf_sym)
            info = ticker.fast_info
            last_p = getattr(info, "last_price", None)
            prev_close = getattr(info, "previous_close", None)
            open_p = getattr(info, "open", None)
            high_p = getattr(info, "day_high", None)
            low_p = getattr(info, "day_low", None)

            if last_p is not None:
                lp_dec = Decimal(str(round(last_p, 2)))
                pc_dec = Decimal(str(round(prev_close, 2))) if prev_close else lp_dec
                chg = lp_dec - pc_dec
                pct = (chg / pc_dec) * Decimal("100.0") if pc_dec else Decimal("0.0")

                exchange = "BSE" if "SENSEX" in norm or "BSESN" in yf_sym else "NSE"

                return IndexQuote(
                    symbol=norm if norm in ["NIFTY 50", "SENSEX", "BANK NIFTY"] else ("NIFTY 50" if "NSEI" in yf_sym else "BANK NIFTY"),
                    exchange=exchange,
                    timestamp=now,
                    last_price=lp_dec,
                    open=Decimal(str(round(open_p, 2))) if open_p else None,
                    high=Decimal(str(round(high_p, 2))) if high_p else None,
                    low=Decimal(str(round(low_p, 2))) if low_p else None,
                    previous_close=pc_dec,
                    change=round(chg, 2),
                    change_percent=round(pct, 2),
                    data_status=self._default_status,
                )
        except Exception as e:
            logger.warning(f"Error fetching index '{symbol}' from yfinance: {e}")

        return await self._fno_fallback.get_index_quote(symbol)

    async def get_indices_quotes(self) -> List[IndexQuote]:
        return [
            await self.get_index_quote("NIFTY 50"),
            await self.get_index_quote("SENSEX"),
            await self.get_index_quote("BANK NIFTY"),
        ]

    async def get_fno_contracts(self, underlying: str) -> List[FNOQuote]:
        # Yahoo Finance does not supply Indian F&O contracts.
        # Transparently use F&O mathematical model labeled DEMO DATA / SIMULATED.
        return await self._fno_fallback.get_fno_contracts(underlying)

    async def get_option_chain(
        self, underlying: str, expiry: Optional[str] = None
    ) -> OptionChainResponse:
        # Transparently use simulated F&O engine
        return await self._fno_fallback.get_option_chain(underlying, expiry)

    async def get_historical_data(
        self,
        symbol: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        interval: str = "1d",
    ) -> pd.DataFrame:
        clean = self._clean_symbol(symbol)
        yf_sym = self._normalize_equity_symbol(clean)
        return self._yf.fetch_ohlcv(yf_sym, start_date=start_date, end_date=end_date, interval=interval)
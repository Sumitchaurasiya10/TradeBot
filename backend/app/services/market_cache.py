import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional
import pytz

from backend.app.schemas.market import DataStatus, IndexQuote, OptionChainResponse, Quote

IST = pytz.timezone("Asia/Kolkata")


class LiveMarketCache:
    """
    In-memory cache for real-time market data.
    Provides fast O(1) reads for WebSocket broadcasters and REST endpoints.
    Includes automatic staleness tracking: if cached data exceeds `stale_threshold_seconds`,
    it is served with DataStatus.STALE rather than pretending to be live.
    """

    def __init__(self, stale_threshold_seconds: int = 3600):
        self._quotes: Dict[str, Quote] = {}
        self._indices: Dict[str, IndexQuote] = {}
        self._option_chains: Dict[str, OptionChainResponse] = {}
        self._stale_threshold = stale_threshold_seconds
        self._lock = asyncio.Lock()

    def _normalize_symbol(self, symbol: str) -> str:
        return symbol.upper().replace(".NS", "").replace(".BO", "").strip()

    def _is_stale(self, timestamp: datetime) -> bool:
        now = datetime.now(timezone.utc)
        if timestamp.tzinfo is None:
            ts_utc = timestamp.replace(tzinfo=timezone.utc)
        else:
            ts_utc = timestamp.astimezone(timezone.utc)
        age = (now - ts_utc).total_seconds()
        return age > self._stale_threshold

    async def set_quote(self, quote: Quote) -> None:
        async with self._lock:
            key = self._normalize_symbol(quote.symbol)
            self._quotes[key] = quote

    async def set_quotes(self, quotes: List[Quote]) -> None:
        async with self._lock:
            for q in quotes:
                key = self._normalize_symbol(q.symbol)
                self._quotes[key] = q

    async def get_quote(self, symbol: str) -> Optional[Quote]:
        async with self._lock:
            key = self._normalize_symbol(symbol)
            quote = self._quotes.get(key)
            if not quote:
                return None

            # Check staleness
            if self._is_stale(quote.timestamp) and quote.data_status not in [DataStatus.DEMO_DATA, DataStatus.SIMULATED]:
                stale_quote = quote.model_copy()
                stale_quote.data_status = DataStatus.STALE
                return stale_quote
            return quote

    async def get_all_quotes(self) -> List[Quote]:
        async with self._lock:
            result = []
            for quote in self._quotes.values():
                if self._is_stale(quote.timestamp) and quote.data_status not in [DataStatus.DEMO_DATA, DataStatus.SIMULATED]:
                    sq = quote.model_copy()
                    sq.data_status = DataStatus.STALE
                    result.append(sq)
                else:
                    result.append(quote)
            return result

    async def set_index_quote(self, index: IndexQuote) -> None:
        async with self._lock:
            key = index.symbol.upper().strip()
            self._indices[key] = index

    async def set_indices_quotes(self, indices: List[IndexQuote]) -> None:
        async with self._lock:
            for idx in indices:
                key = idx.symbol.upper().strip()
                self._indices[key] = idx

    async def get_index_quote(self, symbol: str) -> Optional[IndexQuote]:
        async with self._lock:
            key = symbol.upper().strip()
            idx = self._indices.get(key)
            if not idx:
                return None
            if self._is_stale(idx.timestamp) and idx.data_status not in [DataStatus.DEMO_DATA, DataStatus.SIMULATED]:
                sidx = idx.model_copy()
                sidx.data_status = DataStatus.STALE
                return sidx
            return idx

    async def get_all_indices(self) -> List[IndexQuote]:
        async with self._lock:
            result = []
            for idx in self._indices.values():
                if self._is_stale(idx.timestamp) and idx.data_status not in [DataStatus.DEMO_DATA, DataStatus.SIMULATED]:
                    sidx = idx.model_copy()
                    sidx.data_status = DataStatus.STALE
                    result.append(sidx)
                else:
                    result.append(idx)
            return result

    async def set_option_chain(self, chain: OptionChainResponse) -> None:
        async with self._lock:
            key = f"{self._normalize_symbol(chain.underlying)}:{chain.expiry}"
            self._option_chains[key] = chain

    async def get_option_chain(self, underlying: str, expiry: Optional[str] = None) -> Optional[OptionChainResponse]:
        async with self._lock:
            clean = self._normalize_symbol(underlying)
            if expiry:
                key = f"{clean}:{expiry}"
                return self._option_chains.get(key)
            # Find earliest available cached expiry for this underlying
            for k, chain in self._option_chains.items():
                if k.startswith(f"{clean}:"):
                    return chain
            return None

    async def clear(self) -> None:
        async with self._lock:
            self._quotes.clear()
            self._indices.clear()
            self._option_chains.clear()


# Global singleton instance
market_cache = LiveMarketCache()
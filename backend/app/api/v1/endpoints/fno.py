from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from backend.app.core.config import settings
from backend.app.schemas.market import (
    DataStatus,
    FNOQuote,
    OptionChainResponse,
)
from backend.app.services.market_cache import market_cache
from backend.app.services.market_data import get_market_data_provider
from backend.app.services.market_data.base import MarketDataProvider

router = APIRouter()


@router.get("/underlyings", summary="Get Supported F&O Underlyings")
async def get_fno_underlyings(
    provider: MarketDataProvider = Depends(get_market_data_provider),
):
    """
    Returns list of supported F&O underlying instruments (Indices and Equities)
    with their current spot prices.
    """
    underlyings_meta = []
    for item in settings.SUPPORTED_FNO_UNDERLYINGS:
        clean = item.upper().strip()
        is_index = "NIFTY" in clean

        # Get spot price
        if is_index:
            idx_name = "NIFTY 50" if clean == "NIFTY" else ("BANK NIFTY" if "BANK" in clean else clean)
            idx_q = await provider.get_index_quote(idx_name)
            spot = idx_q.last_price
            data_status = idx_q.data_status
        else:
            eq_q = await provider.get_quote(clean)
            spot = eq_q.last_price
            data_status = eq_q.data_status

        underlyings_meta.append({
            "underlying": clean,
            "type": "INDEX" if is_index else "EQUITY",
            "spot_price": spot,
            "data_status": data_status,
        })

    return underlyings_meta


@router.get("/expiries/{underlying}", response_model=List[str], summary="Get Available Expiries for Underlying")
async def get_fno_expiries(
    underlying: str,
    provider: MarketDataProvider = Depends(get_market_data_provider),
):
    """
    Returns all active expiry dates (weekly and monthly) for a selected underlying.
    """
    clean = underlying.upper().strip()
    chain = await provider.get_option_chain(clean)
    return chain.available_expiries


@router.get("/option-chain/{underlying}", response_model=OptionChainResponse, summary="Get Full Option Chain")
async def get_option_chain(
    underlying: str,
    expiry: Optional[str] = Query(None, description="Target expiry date (YYYY-MM-DD). Defaults to nearest active expiry."),
    force_refresh: bool = False,
    provider: MarketDataProvider = Depends(get_market_data_provider),
):
    """
    Returns complete strike-by-strike Option Chain (Calls and Puts side-by-side)
    with Open Interest, Change in OI, LTP, Bid/Ask, and Volume.
    """
    clean = underlying.upper().strip()

    if not force_refresh:
        cached = await market_cache.get_option_chain(clean, expiry=expiry)
        if cached and cached.data_status != DataStatus.STALE:
            return cached

    chain = await provider.get_option_chain(clean, expiry=expiry)
    await market_cache.set_option_chain(chain)
    return chain


@router.get("/contracts/{underlying}", response_model=List[FNOQuote], summary="Get All F&O Contracts for Underlying")
async def get_fno_contracts(
    underlying: str,
    provider: MarketDataProvider = Depends(get_market_data_provider),
):
    """
    Returns flattened list of all Call, Put, and Futures contracts for an underlying.
    """
    clean = underlying.upper().strip()
    return await provider.get_fno_contracts(clean)
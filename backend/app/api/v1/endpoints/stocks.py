import pandas as pd
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.config import settings
from backend.app.database.session import get_db
from backend.app.models.stock import Stock
from backend.app.schemas.stock import (
    IndicatorDataPoint,
    IndicatorResponse,
    MarketDataPoint,
    MarketDataResponse,
    StockResponse,
)
from backend.app.services.data_ingestion import DataIngestionService
from backend.app.services.data_validator import DataValidationError, DataValidator
from backend.app.services.indicator_service import IndicatorService

router = APIRouter()
ingestion_service = DataIngestionService()


@router.get("", response_model=List[StockResponse])
async def get_stocks(db: AsyncSession = Depends(get_db)):
    """List all supported NSE stocks."""
    result = await db.execute(select(Stock).where(Stock.is_active == True))
    stocks = result.scalars().all()
    return stocks


@router.get("/{symbol}/market-data", response_model=MarketDataResponse)
async def get_market_data(
    symbol: str,
    force_refresh: bool = Query(default=False, description="Bypass cache and fetch latest from provider"),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve historical OHLCV data for an NSE stock.
    Uses cached database bars if available, otherwise ingests from provider.
    """
    try:
        clean_symbol = DataValidator.validate_symbol(symbol)
        df = await ingestion_service.get_or_fetch_market_data(
            session=db,
            symbol=clean_symbol,
            force_refresh=force_refresh,
        )

        bars = [
            MarketDataPoint(
                timestamp=str(row["timestamp"]),
                open=round(float(row["open"]), 2),
                high=round(float(row["high"]), 2),
                low=round(float(row["low"]), 2),
                close=round(float(row["close"]), 2),
                volume=int(row["volume"]),
            )
            for _, row in df.iterrows()
        ]

        return MarketDataResponse(
            symbol=clean_symbol,
            data_provider=settings.MARKET_DATA_PROVIDER,
            data_status="LATEST_AVAILABLE_DELAYED" if force_refresh else "HISTORICAL",
            count=len(bars),
            bars=bars,
        )

    except DataValidationError as dve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(dve))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve market data for '{symbol}': {str(e)}",
        )


@router.get("/{symbol}/indicators", response_model=IndicatorResponse)
async def get_indicators(
    symbol: str,
    fast_ema: int = Query(default=9, ge=2, le=50),
    slow_ema: int = Query(default=21, ge=3, le=200),
    rsi: int = Query(default=14, ge=2, le=50),
    volume_ma: int = Query(default=20, ge=2, le=100),
    db: AsyncSession = Depends(get_db),
):
    """
    Calculates and returns EMA, RSI, and Volume MA indicators on the OHLCV series.
    """
    if fast_ema >= slow_ema:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"fast_ema ({fast_ema}) must be less than slow_ema ({slow_ema})",
        )

    try:
        clean_symbol = DataValidator.validate_symbol(symbol)
        df = await ingestion_service.get_or_fetch_market_data(session=db, symbol=clean_symbol)
        enriched_df = IndicatorService.enrich_dataframe(
            df=df,
            fast_ema_period=fast_ema,
            slow_ema_period=slow_ema,
            rsi_period=rsi,
            volume_ma_period=volume_ma,
        )

        bars = []
        for _, row in enriched_df.iterrows():
            f_ema = row[f"ema_{fast_ema}"]
            s_ema = row[f"ema_{slow_ema}"]
            rsi_val = row[f"rsi_{rsi}"]
            v_ma = row[f"volume_ma_{volume_ma}"]

            bars.append(IndicatorDataPoint(
                timestamp=str(row["timestamp"]),
                open=round(float(row["open"]), 2),
                high=round(float(row["high"]), 2),
                low=round(float(row["low"]), 2),
                close=round(float(row["close"]), 2),
                volume=int(row["volume"]),
                fast_ema=round(float(f_ema), 2) if not pd.isna(f_ema) else None,
                slow_ema=round(float(s_ema), 2) if not pd.isna(s_ema) else None,
                rsi=round(float(rsi_val), 2) if not pd.isna(rsi_val) else None,
                volume_ma=round(float(v_ma), 2) if not pd.isna(v_ma) else None,
            ))

        return IndicatorResponse(
            symbol=clean_symbol,
            fast_ema_period=fast_ema,
            slow_ema_period=slow_ema,
            rsi_period=rsi,
            volume_ma_period=volume_ma,
            bars=bars,
        )
    except DataValidationError as dve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(dve))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate indicators for '{symbol}': {str(e)}",
        )

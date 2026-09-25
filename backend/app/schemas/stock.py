from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class StockResponse(BaseModel):
    id: int
    symbol: str
    company_name: str
    sector: Optional[str]
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class MarketDataPoint(BaseModel):
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: int


class MarketDataResponse(BaseModel):
    symbol: str
    data_provider: str
    data_status: str  # "HISTORICAL", "LATEST_AVAILABLE_DELAYED", "SIMULATED"
    count: int
    bars: List[MarketDataPoint]


class IndicatorDataPoint(BaseModel):
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    fast_ema: Optional[float]
    slow_ema: Optional[float]
    rsi: Optional[float]
    volume_ma: Optional[float]


class IndicatorResponse(BaseModel):
    symbol: str
    fast_ema_period: int
    slow_ema_period: int
    rsi_period: int
    volume_ma_period: int
    bars: List[IndicatorDataPoint]

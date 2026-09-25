from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class SignalRequest(BaseModel):
    symbol: str = "TCS.NS"
    fast_ema_period: int = Field(default=9, ge=2, le=50)
    slow_ema_period: int = Field(default=21, ge=3, le=200)
    rsi_period: int = Field(default=14, ge=2, le=50)
    rsi_entry_threshold: float = Field(default=50.0, ge=10.0, le=90.0)
    rsi_max_threshold: float = Field(default=85.0, ge=50.0, le=100.0)
    rsi_exit_threshold: float = Field(default=45.0, ge=10.0, le=90.0)
    volume_ma_period: int = Field(default=20, ge=2, le=100)
    volume_multiplier: float = Field(default=1.0, ge=0.1, le=5.0)


class SignalResponse(BaseModel):
    signal: str  # "BUY", "SELL", "HOLD"
    timestamp: str
    symbol: str
    reason: str
    indicators: Dict[str, Optional[float]]
    parameters: Dict[str, Any]

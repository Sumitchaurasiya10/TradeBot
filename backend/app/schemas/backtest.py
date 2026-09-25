from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class BacktestRequest(BaseModel):
    symbol: str = "TCS.NS"
    initial_capital: float = Field(default=100000.0, ge=1000.0)
    fast_ema_period: int = Field(default=9, ge=2, le=50)
    slow_ema_period: int = Field(default=21, ge=3, le=200)
    rsi_period: int = Field(default=14, ge=2, le=50)
    rsi_entry_threshold: float = Field(default=50.0, ge=10.0, le=90.0)
    rsi_max_threshold: float = Field(default=85.0, ge=50.0, le=100.0)
    rsi_exit_threshold: float = Field(default=45.0, ge=10.0, le=90.0)
    volume_ma_period: int = Field(default=20, ge=2, le=100)
    volume_multiplier: float = Field(default=1.0, ge=0.1, le=5.0)
    stop_loss_pct: float = Field(default=0.02, ge=0.005, le=0.20)
    take_profit_pct: float = Field(default=0.05, ge=0.01, le=0.50)
    position_size_pct: float = Field(default=0.20, ge=0.05, le=1.00)


class BacktestTradeResponse(BaseModel):
    trade_id: int
    symbol: str
    entry_timestamp: str
    exit_timestamp: str
    entry_price: float
    exit_price: float
    quantity: int
    gross_pnl: float
    net_pnl: float
    fees_paid: float
    return_pct: float
    exit_reason: str


class EquityPointResponse(BaseModel):
    timestamp: str
    equity: float
    cash: float
    drawdown_pct: float


class BacktestResponse(BaseModel):
    id: Optional[int] = None
    symbol: str
    strategy_name: str
    parameters: Dict[str, Any]
    initial_capital: float
    final_equity: float
    total_return_pct: float
    benchmark_return_pct: float  # Buy-and-Hold
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate_pct: float
    average_trade_return_pct: float
    max_drawdown_pct: float
    profit_factor: float
    total_transaction_costs: float
    equity_curve: List[EquityPointResponse] = Field(default_factory=list)
    trades: List[BacktestTradeResponse] = Field(default_factory=list)

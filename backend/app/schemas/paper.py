from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field


class OrderCreateRequest(BaseModel):
    symbol: str
    side: str  # "BUY" or "SELL"
    quantity: int = Field(gt=0)
    price: Optional[float] = Field(default=0.0, ge=0.0, description="Order price, or 0.0 to auto-fill at current market LTP")
    stop_loss_pct: Optional[float] = Field(default=None, ge=0.005, le=0.20)
    take_profit_pct: Optional[float] = Field(default=None, ge=0.01, le=0.50)


class OrderResponse(BaseModel):
    order_id: int
    symbol: str
    side: str
    quantity: int
    requested_price: float
    executed_price: Optional[float]
    status: str
    fees: float
    timestamp: str
    rejection_reason: Optional[str]


class PositionResponse(BaseModel):
    symbol: str
    quantity: int
    average_entry_price: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    stop_loss_price: Optional[float]
    take_profit_price: Optional[float]


class TradeResponse(BaseModel):
    trade_id: int
    order_id: int
    symbol: str
    side: str
    quantity: int
    price: float
    fees: float
    realized_pnl: Optional[float]
    timestamp: str


class PortfolioSummaryResponse(BaseModel):
    account_name: str
    currency: str
    initial_balance: float
    cash: float
    total_equity: float
    realized_pnl: float
    unrealized_pnl: float
    total_pnl: float
    total_fees_paid: float
    open_positions_count: int
    positions: List[PositionResponse]

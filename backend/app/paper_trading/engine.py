from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from backend.app.backtesting.cost_model import TransactionCostModel
from backend.app.core.config import settings
from backend.app.paper_trading.risk_manager import RiskManager, RiskValidationError


class PaperOrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class PaperOrderStatus(str, Enum):
    FILLED = "FILLED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class PaperOrder(BaseModel):
    order_id: int
    symbol: str
    side: PaperOrderSide
    quantity: int
    requested_price: Decimal
    executed_price: Optional[Decimal] = None
    status: PaperOrderStatus
    fees: Decimal = Decimal("0.0")
    timestamp: str
    rejection_reason: Optional[str] = None


class PaperTrade(BaseModel):
    trade_id: int
    order_id: int
    symbol: str
    side: PaperOrderSide
    quantity: int
    price: Decimal
    fees: Decimal
    realized_pnl: Optional[Decimal] = None
    timestamp: str


class PaperPosition(BaseModel):
    symbol: str
    quantity: int
    average_entry_price: Decimal
    current_price: Decimal
    unrealized_pnl: Decimal = Decimal("0.0")
    realized_pnl: Decimal = Decimal("0.0")
    stop_loss_price: Optional[Decimal] = None
    take_profit_price: Optional[Decimal] = None

    def update_price(self, new_price: Decimal):
        self.current_price = new_price
        self.unrealized_pnl = (new_price - self.average_entry_price) * Decimal(self.quantity)


class PaperTradingEngine:
    """
    Simulated Paper Trading Engine.
    Manages a single paper account with cash ledger, position accounting,
    order validation, and risk control.
    """

    def __init__(
        self,
        initial_balance: Optional[Decimal] = None,
        cost_model: Optional[TransactionCostModel] = None,
        risk_manager: Optional[RiskManager] = None,
    ):
        self.initial_balance = initial_balance or settings.DEFAULT_INITIAL_CAPITAL
        self.cash = self.initial_balance
        self.cost_model = cost_model or TransactionCostModel()
        self.risk_manager = risk_manager or RiskManager()

        self.positions: Dict[str, PaperPosition] = {}
        self.orders: List[PaperOrder] = []
        self.trades: List[PaperTrade] = []
        self._order_counter = 0
        self._trade_counter = 0
        self.total_realized_pnl = Decimal("0.0")
        self.total_fees_paid = Decimal("0.0")

    @property
    def total_unrealized_pnl(self) -> Decimal:
        return sum((p.unrealized_pnl for p in self.positions.values()), Decimal("0.0"))

    @property
    def total_equity(self) -> Decimal:
        position_market_value = sum(
            (p.current_price * Decimal(p.quantity) for p in self.positions.values()),
            Decimal("0.0")
        )
        return self.cash + position_market_value

    def update_market_price(self, symbol: str, current_price: Decimal) -> None:
        """Updates the current market price of an open position for unrealized P&L."""
        if symbol in self.positions:
            self.positions[symbol].update_price(current_price)

    def place_order(
        self,
        symbol: str,
        side: str,
        quantity: int,
        price: Decimal,
        stop_loss_pct: Optional[Decimal] = None,
        take_profit_pct: Optional[Decimal] = None,
    ) -> PaperOrder:
        """
        Processes and validates an order, updating the paper portfolio state.
        """
        self._order_counter += 1
        order_id = self._order_counter
        timestamp_now = datetime.now(timezone.utc).isoformat()
        side_upper = side.upper()

        # 1. Basic validation
        if symbol not in settings.SUPPORTED_SYMBOLS:
            order = PaperOrder(
                order_id=order_id,
                symbol=symbol,
                side=PaperOrderSide(side_upper) if side_upper in [PaperOrderSide.BUY.value, PaperOrderSide.SELL.value] else PaperOrderSide.BUY,
                quantity=quantity,
                requested_price=price,
                status=PaperOrderStatus.REJECTED,
                timestamp=timestamp_now,
                rejection_reason=f"Symbol '{symbol}' is not in supported universe {settings.SUPPORTED_SYMBOLS}",
            )
            self.orders.append(order)
            return order

        if quantity <= 0:
            order = PaperOrder(
                order_id=order_id,
                symbol=symbol,
                side=PaperOrderSide(side_upper),
                quantity=quantity,
                requested_price=price,
                status=PaperOrderStatus.REJECTED,
                timestamp=timestamp_now,
                rejection_reason=f"Quantity must be strictly positive, got {quantity}",
            )
            self.orders.append(order)
            return order

        if price <= Decimal("0.0"):
            order = PaperOrder(
                order_id=order_id,
                symbol=symbol,
                side=PaperOrderSide(side_upper),
                quantity=quantity,
                requested_price=price,
                status=PaperOrderStatus.REJECTED,
                timestamp=timestamp_now,
                rejection_reason=f"Price must be strictly positive, got {price}",
            )
            self.orders.append(order)
            return order

        # 2. BUY execution branch
        if side_upper == PaperOrderSide.BUY.value:
            is_new = symbol not in self.positions or self.positions[symbol].quantity == 0

            # Risk validation
            try:
                self.risk_manager.validate_buy_order(
                    symbol=symbol,
                    price=price,
                    quantity=quantity,
                    current_cash=self.cash,
                    total_equity=self.total_equity,
                    current_open_positions_count=len(self.positions),
                    is_new_position=is_new,
                )
            except RiskValidationError as rve:
                order = PaperOrder(
                    order_id=order_id,
                    symbol=symbol,
                    side=PaperOrderSide.BUY,
                    quantity=quantity,
                    requested_price=price,
                    status=PaperOrderStatus.REJECTED,
                    timestamp=timestamp_now,
                    rejection_reason=str(rve),
                )
                self.orders.append(order)
                return order

            exec_price = self.cost_model.get_effective_execution_price("BUY", price)
            costs = self.cost_model.calculate_costs("BUY", exec_price, quantity)
            required_cash = (exec_price * Decimal(quantity)) + costs.total_cost

            if self.cash < required_cash:
                order = PaperOrder(
                    order_id=order_id,
                    symbol=symbol,
                    side=PaperOrderSide.BUY,
                    quantity=quantity,
                    requested_price=price,
                    status=PaperOrderStatus.REJECTED,
                    timestamp=timestamp_now,
                    rejection_reason=(
                        f"Insufficient simulated cash. Required: ?{required_cash:,.2f} "
                        f"(including ?{costs.total_cost:,.2f} fees), Available: ?{self.cash:,.2f}"
                    ),
                )
                self.orders.append(order)
                return order

            # Deduct cash & record fees
            self.cash -= required_cash
            self.total_fees_paid += costs.total_cost

            sl_price, tp_price = self.risk_manager.calculate_bracket_prices(
                exec_price, stop_loss_pct, take_profit_pct
            )

            # Update position (weighted average price if existing)
            if symbol in self.positions and self.positions[symbol].quantity > 0:
                pos = self.positions[symbol]
                total_qty = pos.quantity + quantity
                total_val = (pos.average_entry_price * Decimal(pos.quantity)) + (exec_price * Decimal(quantity))
                new_avg = round(total_val / Decimal(total_qty), 4)
                pos.quantity = total_qty
                pos.average_entry_price = new_avg
                pos.current_price = exec_price
                pos.stop_loss_price = sl_price
                pos.take_profit_price = tp_price
                pos.update_price(exec_price)
            else:
                self.positions[symbol] = PaperPosition(
                    symbol=symbol,
                    quantity=quantity,
                    average_entry_price=exec_price,
                    current_price=exec_price,
                    stop_loss_price=sl_price,
                    take_profit_price=tp_price,
                )
                self.positions[symbol].update_price(exec_price)

            # Record Trade
            self._trade_counter += 1
            trade = PaperTrade(
                trade_id=self._trade_counter,
                order_id=order_id,
                symbol=symbol,
                side=PaperOrderSide.BUY,
                quantity=quantity,
                price=exec_price,
                fees=costs.total_cost,
                realized_pnl=None,
                timestamp=timestamp_now,
            )
            self.trades.append(trade)

            order = PaperOrder(
                order_id=order_id,
                symbol=symbol,
                side=PaperOrderSide.BUY,
                quantity=quantity,
                requested_price=price,
                executed_price=exec_price,
                status=PaperOrderStatus.FILLED,
                fees=costs.total_cost,
                timestamp=timestamp_now,
            )
            self.orders.append(order)
            return order

        # 3. SELL execution branch
        elif side_upper == PaperOrderSide.SELL.value:
            if symbol not in self.positions or self.positions[symbol].quantity == 0:
                order = PaperOrder(
                    order_id=order_id,
                    symbol=symbol,
                    side=PaperOrderSide.SELL,
                    quantity=quantity,
                    requested_price=price,
                    status=PaperOrderStatus.REJECTED,
                    timestamp=timestamp_now,
                    rejection_reason=f"No open position held for '{symbol}' to sell.",
                )
                self.orders.append(order)
                return order

            pos = self.positions[symbol]
            if quantity > pos.quantity:
                order = PaperOrder(
                    order_id=order_id,
                    symbol=symbol,
                    side=PaperOrderSide.SELL,
                    quantity=quantity,
                    requested_price=price,
                    status=PaperOrderStatus.REJECTED,
                    timestamp=timestamp_now,
                    rejection_reason=(
                        f"Cannot sell {quantity} shares of '{symbol}'. "
                        f"Only {pos.quantity} shares currently held (overselling prevented)."
                    ),
                )
                self.orders.append(order)
                return order

            exec_price = self.cost_model.get_effective_execution_price("SELL", price)
            costs = self.cost_model.calculate_costs("SELL", exec_price, quantity)
            proceeds = (exec_price * Decimal(quantity)) - costs.total_cost

            # Cash proceeds added
            self.cash += proceeds
            self.total_fees_paid += costs.total_cost

            # Calculate Realized P&L
            gross_pnl = (exec_price - pos.average_entry_price) * Decimal(quantity)
            net_pnl = gross_pnl - costs.total_cost
            self.total_realized_pnl += net_pnl

            # Update position quantity
            pos.quantity -= quantity
            pos.realized_pnl += net_pnl
            if pos.quantity == 0:
                del self.positions[symbol]
            else:
                pos.update_price(exec_price)

            self._trade_counter += 1
            trade = PaperTrade(
                trade_id=self._trade_counter,
                order_id=order_id,
                symbol=symbol,
                side=PaperOrderSide.SELL,
                quantity=quantity,
                price=exec_price,
                fees=costs.total_cost,
                realized_pnl=net_pnl,
                timestamp=timestamp_now,
            )
            self.trades.append(trade)

            order = PaperOrder(
                order_id=order_id,
                symbol=symbol,
                side=PaperOrderSide.SELL,
                quantity=quantity,
                requested_price=price,
                executed_price=exec_price,
                status=PaperOrderStatus.FILLED,
                fees=costs.total_cost,
                timestamp=timestamp_now,
            )
            self.orders.append(order)
            return order

        else:
            order = PaperOrder(
                order_id=order_id,
                symbol=symbol,
                side=PaperOrderSide.BUY,
                quantity=quantity,
                requested_price=price,
                status=PaperOrderStatus.REJECTED,
                timestamp=timestamp_now,
                rejection_reason=f"Invalid order side '{side}'. Must be 'BUY' or 'SELL'.",
            )
            self.orders.append(order)
            return order

    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Returns structured portfolio valuation and P&L metrics."""
        return {
            "initial_balance": round(float(self.initial_balance), 2),
            "cash": round(float(self.cash), 2),
            "total_equity": round(float(self.total_equity), 2),
            "realized_pnl": round(float(self.total_realized_pnl), 2),
            "unrealized_pnl": round(float(self.total_unrealized_pnl), 2),
            "total_pnl": round(float(self.total_realized_pnl + self.total_unrealized_pnl), 2),
            "total_fees_paid": round(float(self.total_fees_paid), 2),
            "open_positions_count": len(self.positions),
            "total_orders": len(self.orders),
            "total_trades": len(self.trades),
            "positions": [
                {
                    "symbol": p.symbol,
                    "quantity": p.quantity,
                    "average_entry_price": round(float(p.average_entry_price), 2),
                    "current_price": round(float(p.current_price), 2),
                    "market_value": round(float(p.current_price * Decimal(p.quantity)), 2),
                    "unrealized_pnl": round(float(p.unrealized_pnl), 2),
                    "stop_loss_price": round(float(p.stop_loss_price), 2) if p.stop_loss_price else None,
                    "take_profit_price": round(float(p.take_profit_price), 2) if p.take_profit_price else None,
                }
                for p in self.positions.values()
            ],
        }

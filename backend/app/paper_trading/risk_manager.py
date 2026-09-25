from decimal import Decimal
from typing import Optional
from backend.app.core.config import settings


class RiskValidationError(Exception):
    """Raised when an order violates risk management rules."""
    pass


class RiskManager:
    """
    Evaluates order proposals against configurable risk rules.
    Educational software features designed to safeguard simulated portfolio capital.
    """

    def __init__(
        self,
        max_capital_per_trade_pct: Decimal = Decimal("0.20"),  # Max 20% of capital in one stock
        max_open_positions: int = 5,
        default_stop_loss_pct: Decimal = Decimal("0.02"),      # 2% stop-loss
        default_take_profit_pct: Decimal = Decimal("0.05"),    # 5% take-profit
    ):
        self.max_capital_per_trade_pct = max_capital_per_trade_pct
        self.max_open_positions = max_open_positions
        self.default_stop_loss_pct = default_stop_loss_pct
        self.default_take_profit_pct = default_take_profit_pct

    def validate_buy_order(
        self,
        symbol: str,
        price: Decimal,
        quantity: int,
        current_cash: Decimal,
        total_equity: Decimal,
        current_open_positions_count: int,
        is_new_position: bool,
    ) -> None:
        """
        Validates whether a BUY order complies with portfolio risk rules.
        """
        if quantity <= 0:
            raise RiskValidationError(f"Order quantity must be positive, got {quantity}")

        if price <= Decimal("0.0"):
            raise RiskValidationError(f"Order price must be positive, got {price}")

        # 1. Check max open positions limit
        if is_new_position and current_open_positions_count >= self.max_open_positions:
            raise RiskValidationError(
                f"Cannot open new position for '{symbol}'. Maximum open positions limit ({self.max_open_positions}) reached."
            )

        # 2. Check maximum capital allocation per trade
        order_value = price * Decimal(quantity)
        max_allowed_allocation = total_equity * self.max_capital_per_trade_pct

        if order_value > max_allowed_allocation:
            raise RiskValidationError(
                f"Order value (₹{order_value:,.2f}) exceeds maximum allowed capital allocation per trade "
                f"(₹{max_allowed_allocation:,.2f}, {float(self.max_capital_per_trade_pct * 100):.1f}% of total equity)."
            )

    def calculate_bracket_prices(
        self,
        entry_price: Decimal,
        custom_stop_loss_pct: Optional[Decimal] = None,
        custom_take_profit_pct: Optional[Decimal] = None,
    ) -> tuple[Decimal, Decimal]:
        """
        Calculates Stop-Loss and Take-Profit price levels.
        """
        sl_pct = custom_stop_loss_pct if custom_stop_loss_pct is not None else self.default_stop_loss_pct
        tp_pct = custom_take_profit_pct if custom_take_profit_pct is not None else self.default_take_profit_pct

        stop_loss_price = round(entry_price * (Decimal("1.0") - sl_pct), 2)
        take_profit_price = round(entry_price * (Decimal("1.0") + tp_pct), 2)

        return stop_loss_price, take_profit_price

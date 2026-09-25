from decimal import Decimal
from typing import Dict
from pydantic import BaseModel


class CostBreakdown(BaseModel):
    brokerage: Decimal
    stt: Decimal
    exchange_charges: Decimal
    gst: Decimal
    stamp_duty: Decimal
    slippage: Decimal
    total_cost: Decimal


class TransactionCostModel:
    """
    Configurable Indian equity transaction cost and slippage model.
    Clearly labeled as an educational approximation for paper trading / backtesting.
    """

    def __init__(
        self,
        brokerage_pct: Decimal = Decimal("0.0003"),    # 0.03%
        stt_pct: Decimal = Decimal("0.001"),           # 0.1% for equity delivery (buy & sell)
        exchange_turnover_pct: Decimal = Decimal("0.0000345"), # ~0.00345% NSE
        gst_pct: Decimal = Decimal("0.18"),            # 18% on (brokerage + turnover)
        stamp_duty_buy_pct: Decimal = Decimal("0.00015"), # 0.015% on buy only
        slippage_pct: Decimal = Decimal("0.0005"),     # 0.05% estimated execution slippage
    ):
        self.brokerage_pct = brokerage_pct
        self.stt_pct = stt_pct
        self.exchange_turnover_pct = exchange_turnover_pct
        self.gst_pct = gst_pct
        self.stamp_duty_buy_pct = stamp_duty_buy_pct
        self.slippage_pct = slippage_pct

    def calculate_costs(self, side: str, price: Decimal, quantity: int) -> CostBreakdown:
        """
        Calculates all Indian statutory charges, brokerage, and slippage for an order.
        """
        turnover = price * Decimal(quantity)
        side_upper = side.upper()

        # 1. Brokerage
        brokerage = round(turnover * self.brokerage_pct, 4)

        # 2. STT (Securities Transaction Tax) - 0.1% on delivery (both Buy & Sell)
        stt = round(turnover * self.stt_pct, 4)

        # 3. Exchange Turnover / SEBI charges
        exchange_charges = round(turnover * self.exchange_turnover_pct, 4)

        # 4. GST - 18% on (brokerage + exchange charges)
        gst = round((brokerage + exchange_charges) * self.gst_pct, 4)

        # 5. Stamp duty - 0.015% on buy only
        stamp_duty = round(turnover * self.stamp_duty_buy_pct, 4) if side_upper == "BUY" else Decimal("0.0")

        # 6. Slippage impact
        slippage = round(turnover * self.slippage_pct, 4)

        total_cost = brokerage + stt + exchange_charges + gst + stamp_duty + slippage

        return CostBreakdown(
            brokerage=brokerage,
            stt=stt,
            exchange_charges=exchange_charges,
            gst=gst,
            stamp_duty=stamp_duty,
            slippage=slippage,
            total_cost=total_cost,
        )

    def get_effective_execution_price(self, side: str, base_price: Decimal) -> Decimal:
        """
        Returns price adjusted for estimated slippage:
        - BUY: Pay slightly higher (+ slippage)
        - SELL: Receive slightly lower (- slippage)
        """
        if side.upper() == "BUY":
            return round(base_price * (Decimal("1.0") + self.slippage_pct), 4)
        else:
            return round(base_price * (Decimal("1.0") - self.slippage_pct), 4)

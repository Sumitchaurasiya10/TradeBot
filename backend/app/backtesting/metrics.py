from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class BacktestTradeRecord(BaseModel):
    trade_id: int
    symbol: str
    entry_timestamp: str
    exit_timestamp: str
    entry_price: Decimal
    exit_price: Decimal
    quantity: int
    gross_pnl: Decimal
    net_pnl: Decimal
    fees_paid: Decimal
    return_pct: float
    exit_reason: str  # "SIGNAL", "STOP_LOSS", "TAKE_PROFIT", "END_OF_DATA"


class EquityPoint(BaseModel):
    timestamp: str
    equity: Decimal
    cash: Decimal
    drawdown_pct: float


class BacktestResult(BaseModel):
    symbol: str
    strategy_name: str
    parameters: Dict[str, Any]
    initial_capital: Decimal
    final_equity: Decimal
    total_return_pct: float
    benchmark_return_pct: float  # Buy-and-Hold
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate_pct: float
    average_trade_return_pct: float
    max_drawdown_pct: float
    profit_factor: float
    total_transaction_costs: Decimal
    equity_curve: List[EquityPoint] = Field(default_factory=list)
    trades: List[BacktestTradeRecord] = Field(default_factory=list)


class MetricsCalculator:
    """
    Computes performance metrics from chronological trade history and equity curve.
    """

    @staticmethod
    def calculate_max_drawdown(equity_series: List[Decimal]) -> float:
        if not equity_series:
            return 0.0

        peak = equity_series[0]
        max_dd = Decimal("0.0")

        for eq in equity_series:
            if eq > peak:
                peak = eq
            if peak > Decimal("0.0"):
                dd = (peak - eq) / peak
                if dd > max_dd:
                    max_dd = dd

        return round(float(max_dd * Decimal("100.0")), 2)

    @classmethod
    def compile_results(
        cls,
        symbol: str,
        strategy_name: str,
        parameters: Dict[str, Any],
        initial_capital: Decimal,
        final_equity: Decimal,
        benchmark_initial_price: Decimal,
        benchmark_final_price: Decimal,
        trades: List[BacktestTradeRecord],
        equity_curve: List[EquityPoint],
        total_costs: Decimal,
    ) -> BacktestResult:
        # 1. Total Strategy Return
        total_return_pct = round(
            float(((final_equity - initial_capital) / initial_capital) * Decimal("100.0")), 2
        )

        # 2. Buy-and-Hold Benchmark Return
        if benchmark_initial_price > Decimal("0.0"):
            benchmark_return_pct = round(
                float(((benchmark_final_price - benchmark_initial_price) / benchmark_initial_price) * Decimal("100.0")), 2
            )
        else:
            benchmark_return_pct = 0.0

        # 3. Trade Statistics
        total_trades = len(trades)
        winning_trades = sum(1 for t in trades if t.net_pnl > Decimal("0.0"))
        losing_trades = sum(1 for t in trades if t.net_pnl < Decimal("0.0"))

        win_rate_pct = round((winning_trades / total_trades * 100.0), 2) if total_trades > 0 else 0.0

        trade_returns = [t.return_pct for t in trades]
        avg_trade_return = round(sum(trade_returns) / len(trade_returns), 2) if trade_returns else 0.0

        # 4. Profit Factor = Gross Profits / Gross Losses
        gross_profits = sum((t.gross_pnl for t in trades if t.gross_pnl > Decimal("0.0")), Decimal("0.0"))
        gross_losses = abs(sum((t.gross_pnl for t in trades if t.gross_pnl < Decimal("0.0")), Decimal("0.0")))

        if gross_losses > Decimal("0.0"):
            profit_factor = round(float(gross_profits / gross_losses), 2)
        elif gross_profits > Decimal("0.0"):
            profit_factor = 999.0  # Perfect win record
        else:
            profit_factor = 0.0

        # 5. Maximum Drawdown
        equities = [pt.equity for pt in equity_curve]
        max_dd = cls.calculate_max_drawdown(equities)

        return BacktestResult(
            symbol=symbol,
            strategy_name=strategy_name,
            parameters=parameters,
            initial_capital=initial_capital,
            final_equity=final_equity,
            total_return_pct=total_return_pct,
            benchmark_return_pct=benchmark_return_pct,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate_pct=win_rate_pct,
            average_trade_return_pct=avg_trade_return,
            max_drawdown_pct=max_dd,
            profit_factor=profit_factor,
            total_transaction_costs=total_costs,
            equity_curve=equity_curve,
            trades=trades,
        )

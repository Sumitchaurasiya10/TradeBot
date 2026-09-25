from decimal import Decimal
from typing import Optional
import pandas as pd
from backend.app.backtesting.cost_model import TransactionCostModel
from backend.app.backtesting.metrics import (
    BacktestResult,
    BacktestTradeRecord,
    EquityPoint,
    MetricsCalculator,
)
from backend.app.strategies.base import BaseStrategy, SignalType


class BacktestEngine:
    """
    Chronological bar-by-bar backtester.
    Enforces strict zero look-ahead bias:
    - Signal calculated on Candle t Close
    - Execution filled on Candle t+1 Open price
    - Conservative intrabar Stop-Loss / Take-Profit handling
    """

    def __init__(
        self,
        strategy: BaseStrategy,
        initial_capital: Decimal = Decimal("100000.00"),
        cost_model: Optional[TransactionCostModel] = None,
        position_size_pct: Decimal = Decimal("0.20"),  # Allocate up to 20% of equity per trade
    ):
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.cost_model = cost_model or TransactionCostModel()
        self.position_size_pct = position_size_pct

    def run(self, df: pd.DataFrame, symbol: str) -> BacktestResult:
        if df is None or len(df) < 5:
            raise ValueError(f"Insufficient data for backtesting symbol '{symbol}'")

        # Ensure sorted chronologically
        df = df.sort_values(by="timestamp").reset_index(drop=True)

        # Generate signals across the dataset using strategy
        signals_df = self.strategy.generate_all_signals(df, symbol)

        cash = self.initial_capital
        position_qty = 0
        entry_price = Decimal("0.0")
        entry_timestamp = ""
        entry_fees = Decimal("0.0")
        stop_loss_price = Decimal("0.0")
        take_profit_price = Decimal("0.0")

        trades = []
        equity_curve = []
        total_transaction_costs = Decimal("0.0")
        trade_counter = 0

        peak_equity = self.initial_capital
        pending_order: Optional[str] = None  # Holds signal from candle t to execute at candle t+1 Open

        for i in range(len(signals_df)):
            row = signals_df.iloc[i]
            timestamp_str = str(row["timestamp"])
            open_p = Decimal(str(round(float(row["open"]), 4)))
            high_p = Decimal(str(round(float(row["high"]), 4)))
            low_p = Decimal(str(round(float(row["low"]), 4)))
            close_p = Decimal(str(round(float(row["close"]), 4)))

            # -------------------------------------------------------------
            # STEP 1: Execute Pending Order from Candle t-1 at Candle t Open
            # -------------------------------------------------------------
            if pending_order == SignalType.BUY.value and position_qty == 0:
                exec_price = self.cost_model.get_effective_execution_price("BUY", open_p)
                allocated_capital = cash * self.position_size_pct
                qty_to_buy = int(allocated_capital // exec_price)

                if qty_to_buy > 0:
                    costs = self.cost_model.calculate_costs("BUY", exec_price, qty_to_buy)
                    required_cash = (exec_price * Decimal(qty_to_buy)) + costs.total_cost

                    if cash >= required_cash:
                        cash -= required_cash
                        position_qty = qty_to_buy
                        entry_price = exec_price
                        entry_timestamp = timestamp_str
                        entry_fees = costs.total_cost
                        total_transaction_costs += costs.total_cost

                        # Set Stop-Loss and Take-Profit price levels
                        sl_pct = Decimal(str(self.strategy.get_parameters().get("stop_loss_pct", 0.02)))
                        tp_pct = Decimal(str(self.strategy.get_parameters().get("take_profit_pct", 0.05)))
                        stop_loss_price = round(entry_price * (Decimal("1.0") - sl_pct), 4)
                        take_profit_price = round(entry_price * (Decimal("1.0") + tp_pct), 4)

            elif pending_order == SignalType.SELL.value and position_qty > 0:
                exec_price = self.cost_model.get_effective_execution_price("SELL", open_p)
                costs = self.cost_model.calculate_costs("SELL", exec_price, position_qty)
                proceeds = (exec_price * Decimal(position_qty)) - costs.total_cost
                cash += proceeds
                total_transaction_costs += costs.total_cost

                # Record completed trade
                trade_counter += 1
                gross_pnl = (exec_price - entry_price) * Decimal(position_qty)
                net_pnl = gross_pnl - entry_fees - costs.total_cost
                return_pct = float(round(((exec_price - entry_price) / entry_price) * Decimal("100.0"), 2))

                trades.append(BacktestTradeRecord(
                    trade_id=trade_counter,
                    symbol=symbol,
                    entry_timestamp=entry_timestamp,
                    exit_timestamp=timestamp_str,
                    entry_price=entry_price,
                    exit_price=exec_price,
                    quantity=position_qty,
                    gross_pnl=gross_pnl,
                    net_pnl=net_pnl,
                    fees_paid=entry_fees + costs.total_cost,
                    return_pct=return_pct,
                    exit_reason="SIGNAL",
                ))

                # Reset position
                position_qty = 0
                entry_price = Decimal("0.0")

            pending_order = None

            # -------------------------------------------------------------
            # STEP 2: Intrabar Stop-Loss / Take-Profit Check for Candle t
            # -------------------------------------------------------------
            if position_qty > 0:
                hit_sl = low_p <= stop_loss_price
                hit_tp = high_p >= take_profit_price

                # Conservative assumption: If both hit in same candle, assume Stop-Loss occurred first
                if hit_sl:
                    exec_price = self.cost_model.get_effective_execution_price("SELL", stop_loss_price)
                    costs = self.cost_model.calculate_costs("SELL", exec_price, position_qty)
                    proceeds = (exec_price * Decimal(position_qty)) - costs.total_cost
                    cash += proceeds
                    total_transaction_costs += costs.total_cost

                    trade_counter += 1
                    gross_pnl = (exec_price - entry_price) * Decimal(position_qty)
                    net_pnl = gross_pnl - entry_fees - costs.total_cost
                    return_pct = float(round(((exec_price - entry_price) / entry_price) * Decimal("100.0"), 2))

                    trades.append(BacktestTradeRecord(
                        trade_id=trade_counter,
                        symbol=symbol,
                        entry_timestamp=entry_timestamp,
                        exit_timestamp=timestamp_str,
                        entry_price=entry_price,
                        exit_price=exec_price,
                        quantity=position_qty,
                        gross_pnl=gross_pnl,
                        net_pnl=net_pnl,
                        fees_paid=entry_fees + costs.total_cost,
                        return_pct=return_pct,
                        exit_reason="STOP_LOSS",
                    ))
                    position_qty = 0
                    entry_price = Decimal("0.0")

                elif hit_tp:
                    exec_price = self.cost_model.get_effective_execution_price("SELL", take_profit_price)
                    costs = self.cost_model.calculate_costs("SELL", exec_price, position_qty)
                    proceeds = (exec_price * Decimal(position_qty)) - costs.total_cost
                    cash += proceeds
                    total_transaction_costs += costs.total_cost

                    trade_counter += 1
                    gross_pnl = (exec_price - entry_price) * Decimal(position_qty)
                    net_pnl = gross_pnl - entry_fees - costs.total_cost
                    return_pct = float(round(((exec_price - entry_price) / entry_price) * Decimal("100.0"), 2))

                    trades.append(BacktestTradeRecord(
                        trade_id=trade_counter,
                        symbol=symbol,
                        entry_timestamp=entry_timestamp,
                        exit_timestamp=timestamp_str,
                        entry_price=entry_price,
                        exit_price=exec_price,
                        quantity=position_qty,
                        gross_pnl=gross_pnl,
                        net_pnl=net_pnl,
                        fees_paid=entry_fees + costs.total_cost,
                        return_pct=return_pct,
                        exit_reason="TAKE_PROFIT",
                    ))
                    position_qty = 0
                    entry_price = Decimal("0.0")

            # -------------------------------------------------------------
            # STEP 3: Generate Signal at Candle t Close for Next Candle Open
            # -------------------------------------------------------------
            signal_curr = row.get("signal", SignalType.HOLD.value)
            if signal_curr == SignalType.BUY.value and position_qty == 0:
                pending_order = SignalType.BUY.value
            elif signal_curr == SignalType.SELL.value and position_qty > 0:
                pending_order = SignalType.SELL.value

            # -------------------------------------------------------------
            # STEP 4: Calculate Mark-to-Market Equity at Candle t Close
            # -------------------------------------------------------------
            current_equity = cash + (Decimal(position_qty) * close_p)
            if current_equity > peak_equity:
                peak_equity = current_equity

            dd_pct = float(round(((peak_equity - current_equity) / peak_equity) * Decimal("100.0"), 2)) if peak_equity > 0 else 0.0

            equity_curve.append(EquityPoint(
                timestamp=timestamp_str,
                equity=round(current_equity, 2),
                cash=round(cash, 2),
                drawdown_pct=dd_pct,
            ))

        # -------------------------------------------------------------
        # STEP 5: Close any remaining open position at the final Close price
        # -------------------------------------------------------------
        if position_qty > 0:
            final_row = signals_df.iloc[-1]
            final_close = Decimal(str(round(float(final_row["close"]), 4)))
            exec_price = self.cost_model.get_effective_execution_price("SELL", final_close)
            costs = self.cost_model.calculate_costs("SELL", exec_price, position_qty)
            cash += (exec_price * Decimal(position_qty)) - costs.total_cost
            total_transaction_costs += costs.total_cost

            trade_counter += 1
            gross_pnl = (exec_price - entry_price) * Decimal(position_qty)
            net_pnl = gross_pnl - entry_fees - costs.total_cost
            return_pct = float(round(((exec_price - entry_price) / entry_price) * Decimal("100.0"), 2))

            trades.append(BacktestTradeRecord(
                trade_id=trade_counter,
                symbol=symbol,
                entry_timestamp=entry_timestamp,
                exit_timestamp=str(final_row["timestamp"]),
                entry_price=entry_price,
                exit_price=exec_price,
                quantity=position_qty,
                gross_pnl=gross_pnl,
                net_pnl=net_pnl,
                fees_paid=entry_fees + costs.total_cost,
                return_pct=return_pct,
                exit_reason="END_OF_DATA",
            ))

        final_equity = cash
        benchmark_initial_price = Decimal(str(round(float(signals_df.iloc[0]["open"]), 4)))
        benchmark_final_price = Decimal(str(round(float(signals_df.iloc[-1]["close"]), 4)))

        return MetricsCalculator.compile_results(
            symbol=symbol,
            strategy_name=self.strategy.__class__.__name__,
            parameters=self.strategy.get_parameters(),
            initial_capital=self.initial_capital,
            final_equity=round(final_equity, 2),
            benchmark_initial_price=benchmark_initial_price,
            benchmark_final_price=benchmark_final_price,
            trades=trades,
            equity_curve=equity_curve,
            total_costs=round(total_transaction_costs, 2),
        )

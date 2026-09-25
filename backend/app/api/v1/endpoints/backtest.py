from datetime import datetime, timezone
from decimal import Decimal
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.backtesting.cost_model import TransactionCostModel
from backend.app.backtesting.engine import BacktestEngine
from backend.app.database.session import get_db
from backend.app.models.backtest import BacktestRun
from backend.app.schemas.backtest import (
    BacktestRequest,
    BacktestResponse,
    BacktestTradeResponse,
    EquityPointResponse,
)
from backend.app.services.data_ingestion import DataIngestionService
from backend.app.services.data_validator import DataValidationError, DataValidator
from backend.app.strategies.ema_rsi_volume import EMARsiVolumeStrategy

router = APIRouter()
ingestion_service = DataIngestionService()


@router.post("", response_model=BacktestResponse)
async def run_backtest(request: BacktestRequest, db: AsyncSession = Depends(get_db)):
    """
    Executes a historical backtest of the EMA + RSI + Volume strategy.
    Enforces zero look-ahead bias (t+1 Open execution).
    Compares against Buy-and-Hold benchmark and persists run metadata.
    """
    if request.fast_ema_period >= request.slow_ema_period:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"fast_ema_period ({request.fast_ema_period}) must be strictly less than slow_ema_period ({request.slow_ema_period})",
        )

    try:
        clean_symbol = DataValidator.validate_symbol(request.symbol)
        df = await ingestion_service.get_or_fetch_market_data(session=db, symbol=clean_symbol)

        strategy = EMARsiVolumeStrategy(
            fast_ema_period=request.fast_ema_period,
            slow_ema_period=request.slow_ema_period,
            rsi_period=request.rsi_period,
            rsi_entry_threshold=request.rsi_entry_threshold,
            rsi_max_threshold=request.rsi_max_threshold,
            rsi_exit_threshold=request.rsi_exit_threshold,
            volume_ma_period=request.volume_ma_period,
            volume_multiplier=request.volume_multiplier,
            stop_loss_pct=request.stop_loss_pct,
            take_profit_pct=request.take_profit_pct,
        )

        cost_model = TransactionCostModel()
        engine = BacktestEngine(
            strategy=strategy,
            initial_capital=Decimal(str(request.initial_capital)),
            cost_model=cost_model,
            position_size_pct=Decimal(str(request.position_size_pct)),
        )

        result = engine.run(df, clean_symbol)

        # Persist run summary to database
        start_dt = df.iloc[0]["timestamp"]
        end_dt = df.iloc[-1]["timestamp"]
        start_pydt = start_dt.to_pydatetime() if hasattr(start_dt, "to_pydatetime") else start_dt
        end_pydt = end_dt.to_pydatetime() if hasattr(end_dt, "to_pydatetime") else end_dt

        db_run = BacktestRun(
            symbol=clean_symbol,
            start_date=start_pydt,
            end_date=end_pydt,
            strategy_name=result.strategy_name,
            parameters=result.parameters,
            initial_capital=result.initial_capital,
            final_capital=result.final_equity,
            total_return_pct=Decimal(str(result.total_return_pct)),
            benchmark_return_pct=Decimal(str(result.benchmark_return_pct)),
            win_rate_pct=Decimal(str(result.win_rate_pct)),
            max_drawdown_pct=Decimal(str(result.max_drawdown_pct)),
            profit_factor=Decimal(str(min(result.profit_factor, 999.0))),
            total_trades=result.total_trades,
            total_fees=result.total_transaction_costs,
        )
        db.add(db_run)
        await db.commit()
        await db.refresh(db_run)

        return BacktestResponse(
            id=db_run.id,
            symbol=result.symbol,
            strategy_name=result.strategy_name,
            parameters=result.parameters,
            initial_capital=float(result.initial_capital),
            final_equity=float(result.final_equity),
            total_return_pct=result.total_return_pct,
            benchmark_return_pct=result.benchmark_return_pct,
            total_trades=result.total_trades,
            winning_trades=result.winning_trades,
            losing_trades=result.losing_trades,
            win_rate_pct=result.win_rate_pct,
            average_trade_return_pct=result.average_trade_return_pct,
            max_drawdown_pct=result.max_drawdown_pct,
            profit_factor=result.profit_factor,
            total_transaction_costs=float(result.total_transaction_costs),
            equity_curve=[
                EquityPointResponse(
                    timestamp=pt.timestamp,
                    equity=float(pt.equity),
                    cash=float(pt.cash),
                    drawdown_pct=pt.drawdown_pct,
                )
                for pt in result.equity_curve
            ],
            trades=[
                BacktestTradeResponse(
                    trade_id=t.trade_id,
                    symbol=t.symbol,
                    entry_timestamp=t.entry_timestamp,
                    exit_timestamp=t.exit_timestamp,
                    entry_price=float(t.entry_price),
                    exit_price=float(t.exit_price),
                    quantity=t.quantity,
                    gross_pnl=float(t.gross_pnl),
                    net_pnl=float(t.net_pnl),
                    fees_paid=float(t.fees_paid),
                    return_pct=t.return_pct,
                    exit_reason=t.exit_reason,
                )
                for t in result.trades
            ],
        )

    except DataValidationError as dve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(dve))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Backtest execution failed: {str(e)}",
        )


@router.get("/{run_id}", response_model=BacktestResponse)
async def get_backtest_run(run_id: int, db: AsyncSession = Depends(get_db)):
    """Retrieve saved backtest run metadata by ID."""
    stmt = select(BacktestRun).where(BacktestRun.id == run_id)
    res = await db.execute(stmt)
    run = res.scalars().first()
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Backtest run #{run_id} not found")

    return BacktestResponse(
        id=run.id,
        symbol=run.symbol,
        strategy_name=run.strategy_name,
        parameters=run.parameters,
        initial_capital=float(run.initial_capital),
        final_equity=float(run.final_capital),
        total_return_pct=float(run.total_return_pct),
        benchmark_return_pct=float(run.benchmark_return_pct),
        total_trades=run.total_trades,
        winning_trades=0,
        losing_trades=0,
        win_rate_pct=float(run.win_rate_pct),
        average_trade_return_pct=0.0,
        max_drawdown_pct=float(run.max_drawdown_pct),
        profit_factor=float(run.profit_factor),
        total_transaction_costs=float(run.total_fees),
        equity_curve=[],
        trades=[],
    )

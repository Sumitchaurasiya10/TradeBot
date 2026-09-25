from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict
from sqlalchemy import DateTime, Integer, JSON, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.database.base import Base


class BacktestRun(Base):
    __tablename__ = "backtest_runs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    strategy_name: Mapped[str] = mapped_column(String(50), nullable=False)
    parameters: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)

    initial_capital: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    final_capital: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    total_return_pct: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)
    benchmark_return_pct: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)
    win_rate_pct: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)
    max_drawdown_pct: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)
    profit_factor: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)
    total_trades: Mapped[int] = mapped_column(Integer, nullable=False)
    total_fees: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

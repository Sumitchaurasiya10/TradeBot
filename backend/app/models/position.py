from decimal import Decimal
from typing import Optional
from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.database.base import Base, TimestampMixin


class Position(Base, TimestampMixin):
    __tablename__ = "positions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("paper_accounts.id"), index=True, nullable=False)
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id"), index=True, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    average_entry_price: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    current_price: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    unrealized_pnl: Mapped[Decimal] = mapped_column(Numeric(12, 4), default=Decimal("0.0"), nullable=False)
    stop_loss_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4), nullable=True)
    take_profit_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4), nullable=True)
    is_open: Mapped[bool] = mapped_column(Boolean, default=True, index=True, nullable=False)

    # Relationships
    account: Mapped["PaperAccount"] = relationship(back_populates="positions")
    stock: Mapped["Stock"] = relationship()

    __table_args__ = (
        UniqueConstraint("account_id", "stock_id", "is_open", name="uq_account_stock_open"),
    )

from decimal import Decimal
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.database.session import get_db
from backend.app.models.account import PaperAccount
from backend.app.models.order import Order
from backend.app.models.position import Position
from backend.app.models.stock import Stock
from backend.app.models.trade import Trade
from backend.app.paper_trading.engine import (
    PaperOrderStatus,
    PaperTradingEngine,
)
from backend.app.schemas.paper import (
    OrderCreateRequest,
    OrderResponse,
    PortfolioSummaryResponse,
    PositionResponse,
    TradeResponse,
)
from backend.app.services.market_data import get_market_data_provider

router = APIRouter()

# Shared paper engine instance for live in-memory portfolio management
paper_engine = PaperTradingEngine()


@router.post("/orders", response_model=OrderResponse)
async def create_paper_order(
    request: OrderCreateRequest,
    db: AsyncSession = Depends(get_db),
    provider=Depends(get_market_data_provider),
):
    """
    Submits a simulated paper market order.
    Enforces risk rules (max allocation, max positions, cash sufficiency, no overselling).
    If price is <= 0, automatically uses the current live market LTP.
    """
    clean = request.symbol.upper().replace(".NS", "").replace(".BO", "").strip()
    is_market = getattr(request, "order_type", "MARKET") == "MARKET" or (request.price is None or request.price <= 0.0)

    if is_market:
        live_q = await provider.get_quote(clean)
        price_dec = live_q.last_price
    else:
        price_dec = Decimal(str(request.price))
    sl_dec = Decimal(str(request.stop_loss_pct)) if request.stop_loss_pct is not None else None
    tp_dec = Decimal(str(request.take_profit_pct)) if request.take_profit_pct is not None else None

    # Execute simulation in paper engine
    sim_order = paper_engine.place_order(
        symbol=request.symbol,
        side=request.side,
        quantity=request.quantity,
        price=price_dec,
        stop_loss_pct=sl_dec,
        take_profit_pct=tp_dec,
    )

    # Persist audit record in database
    stock_res = await db.execute(select(Stock).where(Stock.symbol == request.symbol))
    stock = stock_res.scalars().first()
    acc_res = await db.execute(select(PaperAccount).where(PaperAccount.account_name == "Default Paper Account"))
    account = acc_res.scalars().first()

    if stock and account:
        db_order = Order(
            account_id=account.id,
            stock_id=stock.id,
            side=sim_order.side.value,
            quantity=sim_order.quantity,
            requested_price=sim_order.requested_price,
            executed_price=sim_order.executed_price,
            status=sim_order.status.value,
            fees=sim_order.fees,
            rejection_reason=sim_order.rejection_reason,
        )
        db.add(db_order)
        # Update account cash
        account.current_cash = paper_engine.cash
        await db.commit()

    return OrderResponse(
        order_id=sim_order.order_id,
        symbol=sim_order.symbol,
        side=sim_order.side.value,
        quantity=sim_order.quantity,
        requested_price=float(sim_order.requested_price),
        executed_price=float(sim_order.executed_price) if sim_order.executed_price else None,
        status=sim_order.status.value,
        fees=float(sim_order.fees),
        timestamp=sim_order.timestamp,
        rejection_reason=sim_order.rejection_reason,
    )


@router.get("/portfolio", response_model=PortfolioSummaryResponse)
async def get_portfolio(provider=Depends(get_market_data_provider)):
    """Returns current simulated portfolio valuation, cash balance, and P&L updated with live prices."""
    if paper_engine.positions:
        try:
            pos_syms = list(paper_engine.positions.keys())
            quotes = await provider.get_quotes(pos_syms)
            prices = {q.symbol: q.last_price for q in quotes}
            paper_engine.update_market_prices(prices)
        except Exception:
            pass

    summary = paper_engine.get_portfolio_summary()
    positions = [
        PositionResponse(
            symbol=p["symbol"],
            quantity=p["quantity"],
            average_entry_price=p["average_entry_price"],
            current_price=p["current_price"],
            market_value=p["market_value"],
            unrealized_pnl=p["unrealized_pnl"],
            stop_loss_price=p["stop_loss_price"],
            take_profit_price=p["take_profit_price"],
        )
        for p in summary["positions"]
    ]

    return PortfolioSummaryResponse(
        account_name="Default Paper Account",
        currency="INR",
        initial_balance=summary["initial_balance"],
        cash=summary["cash"],
        total_equity=summary["total_equity"],
        realized_pnl=summary["realized_pnl"],
        unrealized_pnl=summary["unrealized_pnl"],
        total_pnl=summary["total_pnl"],
        total_fees_paid=summary["total_fees_paid"],
        open_positions_count=summary["open_positions_count"],
        positions=positions,
    )


@router.get("/positions", response_model=List[PositionResponse])
async def get_positions(provider=Depends(get_market_data_provider)):
    """Lists all currently active open positions in the paper portfolio updated with live prices."""
    if paper_engine.positions:
        try:
            pos_syms = list(paper_engine.positions.keys())
            quotes = await provider.get_quotes(pos_syms)
            prices = {q.symbol: q.last_price for q in quotes}
            paper_engine.update_market_prices(prices)
        except Exception:
            pass

    summary = paper_engine.get_portfolio_summary()
    return [
        PositionResponse(
            symbol=p["symbol"],
            quantity=p["quantity"],
            average_entry_price=p["average_entry_price"],
            current_price=p["current_price"],
            market_value=p["market_value"],
            unrealized_pnl=p["unrealized_pnl"],
            stop_loss_price=p["stop_loss_price"],
            take_profit_price=p["take_profit_price"],
        )
        for p in summary["positions"]
    ]


@router.get("/trades", response_model=List[TradeResponse])
async def get_trades():
    """Lists full history of executed paper trades."""
    return [
        TradeResponse(
            trade_id=t.trade_id,
            order_id=t.order_id,
            symbol=t.symbol,
            side=t.side.value,
            quantity=t.quantity,
            price=float(t.price),
            fees=float(t.fees),
            realized_pnl=float(t.realized_pnl) if t.realized_pnl is not None else None,
            timestamp=t.timestamp,
        )
        for t in paper_engine.trades
    ]


@router.get("/pnl")
async def get_pnl():
    """Returns summarized profit and loss breakdown."""
    summary = paper_engine.get_portfolio_summary()
    return {
        "realized_pnl": summary["realized_pnl"],
        "unrealized_pnl": summary["unrealized_pnl"],
        "total_pnl": summary["total_pnl"],
        "total_fees_paid": summary["total_fees_paid"],
        "cash": summary["cash"],
        "total_equity": summary["total_equity"],
    }

from decimal import Decimal
import pytest
from backend.app.backtesting.cost_model import TransactionCostModel
from backend.app.paper_trading.engine import PaperOrderStatus, PaperTradingEngine
from backend.app.paper_trading.risk_manager import RiskManager


def test_successful_buy_order():
    cost_model = TransactionCostModel(slippage_pct=Decimal("0.0"))
    engine = PaperTradingEngine(initial_balance=Decimal("100000.00"), cost_model=cost_model)

    # 5 shares @ 3500 = 17,500 (within 20% max allocation limit of 20,000)
    order = engine.place_order(symbol="TCS.NS", side="BUY", quantity=5, price=Decimal("3500.00"))

    assert order.status == PaperOrderStatus.FILLED
    assert order.executed_price == Decimal("3500.00")
    assert order.fees > Decimal("0.0")

    expected_cash = Decimal("100000.00") - (Decimal("17500.00") + order.fees)
    assert engine.cash == expected_cash
    assert "TCS.NS" in engine.positions
    assert engine.positions["TCS.NS"].quantity == 5
    assert len(engine.trades) == 1


def test_insufficient_cash_rejection():
    # Set high allocation tolerance to isolate the cash check
    risk_manager = RiskManager(max_capital_per_trade_pct=Decimal("5.00"))
    engine = PaperTradingEngine(initial_balance=Decimal("5000.00"), risk_manager=risk_manager)

    # Try to buy ₹7,000 worth of TCS with ₹5,000 cash
    order = engine.place_order(symbol="TCS.NS", side="BUY", quantity=2, price=Decimal("3500.00"))

    assert order.status == PaperOrderStatus.REJECTED
    assert "Insufficient simulated cash" in order.rejection_reason
    assert engine.cash == Decimal("5000.00")
    assert len(engine.positions) == 0


def test_successful_sell_order_and_realized_pnl():
    cost_model = TransactionCostModel(slippage_pct=Decimal("0.0"))
    engine = PaperTradingEngine(initial_balance=Decimal("100000.00"), cost_model=cost_model)

    buy_order = engine.place_order(symbol="INFY.NS", side="BUY", quantity=5, price=Decimal("3000.00"))
    assert buy_order.status == PaperOrderStatus.FILLED

    sell_order = engine.place_order(symbol="INFY.NS", side="SELL", quantity=5, price=Decimal("3200.00"))
    assert sell_order.status == PaperOrderStatus.FILLED

    assert "INFY.NS" not in engine.positions
    expected_realized = (Decimal("3200.00") - Decimal("3000.00")) * Decimal(5) - sell_order.fees
    assert engine.total_realized_pnl == expected_realized
    assert len(engine.trades) == 2


def test_overselling_prevention():
    engine = PaperTradingEngine(initial_balance=Decimal("100000.00"))
    engine.place_order(symbol="HDFCBANK.NS", side="BUY", quantity=5, price=Decimal("1500.00"))

    # Attempt to sell 10 shares (only 5 held)
    order = engine.place_order(symbol="HDFCBANK.NS", side="SELL", quantity=10, price=Decimal("1600.00"))

    assert order.status == PaperOrderStatus.REJECTED
    assert "overselling prevented" in order.rejection_reason
    assert engine.positions["HDFCBANK.NS"].quantity == 5


def test_selling_without_holding_rejection():
    engine = PaperTradingEngine(initial_balance=Decimal("100000.00"))
    order = engine.place_order(symbol="ICICIBANK.NS", side="SELL", quantity=5, price=Decimal("1000.00"))

    assert order.status == PaperOrderStatus.REJECTED
    assert "No open position held" in order.rejection_reason


def test_weighted_average_entry_price_when_scaling_in():
    cost_model = TransactionCostModel(slippage_pct=Decimal("0.0"))
    engine = PaperTradingEngine(initial_balance=Decimal("100000.00"), cost_model=cost_model)

    engine.place_order(symbol="RELIANCE.NS", side="BUY", quantity=10, price=Decimal("1000.00"))
    engine.place_order(symbol="RELIANCE.NS", side="BUY", quantity=10, price=Decimal("1200.00"))

    pos = engine.positions["RELIANCE.NS"]
    assert pos.quantity == 20
    assert pos.average_entry_price == Decimal("1100.00")


def test_unrealized_pnl_updates():
    cost_model = TransactionCostModel(slippage_pct=Decimal("0.0"))
    engine = PaperTradingEngine(initial_balance=Decimal("100000.00"), cost_model=cost_model)

    order = engine.place_order(symbol="TCS.NS", side="BUY", quantity=5, price=Decimal("3000.00"))
    assert order.status == PaperOrderStatus.FILLED

    engine.update_market_price("TCS.NS", Decimal("3200.00"))

    pos = engine.positions["TCS.NS"]
    assert pos.unrealized_pnl == Decimal("1000.00")
    assert engine.total_unrealized_pnl == Decimal("1000.00")


def test_risk_manager_max_allocation_rejection():
    risk_manager = RiskManager(max_capital_per_trade_pct=Decimal("0.20"))
    engine = PaperTradingEngine(initial_balance=Decimal("100000.00"), risk_manager=risk_manager)

    # ₹30,000 exceeds 20% limit of ₹20,000
    order = engine.place_order(symbol="TCS.NS", side="BUY", quantity=10, price=Decimal("3000.00"))

    assert order.status == PaperOrderStatus.REJECTED
    assert "exceeds maximum allowed capital allocation" in order.rejection_reason


def test_risk_manager_max_open_positions_rejection():
    risk_manager = RiskManager(max_open_positions=2, max_capital_per_trade_pct=Decimal("0.50"))
    engine = PaperTradingEngine(initial_balance=Decimal("100000.00"), risk_manager=risk_manager)

    o1 = engine.place_order(symbol="RELIANCE.NS", side="BUY", quantity=5, price=Decimal("1000.00"))
    assert o1.status == PaperOrderStatus.FILLED
    o2 = engine.place_order(symbol="TCS.NS", side="BUY", quantity=5, price=Decimal("1000.00"))
    assert o2.status == PaperOrderStatus.FILLED

    # 3rd position must be rejected
    o3 = engine.place_order(symbol="INFY.NS", side="BUY", quantity=5, price=Decimal("1000.00"))
    assert o3.status == PaperOrderStatus.REJECTED
    assert "Maximum open positions limit (2) reached" in o3.rejection_reason


def test_invalid_order_inputs():
    engine = PaperTradingEngine()
    o1 = engine.place_order(symbol="TCS.NS", side="BUY", quantity=-5, price=Decimal("1000.00"))
    assert o1.status == PaperOrderStatus.REJECTED
    o2 = engine.place_order(symbol="TCS.NS", side="BUY", quantity=5, price=Decimal("0.00"))
    assert o2.status == PaperOrderStatus.REJECTED
    o3 = engine.place_order(symbol="UNKNOWN.NS", side="BUY", quantity=5, price=Decimal("1000.00"))
    assert o3.status == PaperOrderStatus.REJECTED

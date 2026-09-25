# TradeBot India: Technical Interview & Architecture Guide

This comprehensive guide answers the key architectural, financial, and engineering questions regarding the Indian Equity Market Paper Trading & Algorithmic Strategy Platform. It is specifically structured for technical interviews, code reviews, and system design discussions.

---

## 1. Why FastAPI?
* **Asynchronous Native Performance (`async`/`await`)**: Trading systems inherently deal with I/O-bound operations—fetching market data feeds from remote endpoints, querying time-series relational tables, and dispatching webhook events. FastAPI is built on Starlette and Uvicorn (ASGI), providing high-throughput concurrency without blocking event loops.
* **Strict Type Safety & Pydantic Validation**: Financial systems cannot tolerate loose typing (e.g., float precision loss, malformed timestamps, or negative order volumes). FastAPI enforces Pydantic v2 schemas at runtime, auto-validating request payloads and serializing responses.
* **Automated OpenAPI / Swagger Documentation**: Generates interactive documentation (`/docs`) out of the box, facilitating rapid frontend-backend contract validation and integration testing.
* **Clean Dependency Injection**: Database sessions, risk management layers, and market data providers are injected cleanly via `fastapi.Depends`, making unit testing and mocking trivial.

---

## 2. Why PostgreSQL?
* **ACID Transactions**: Financial ledger operations (placing orders, deducting cash, creating positions, calculating realized P&L) require strict atomicity, consistency, isolation, and durability. PostgreSQL guarantees no partial writes or state corruption during concurrent order submissions.
* **Relational Integrity & Foreign Key Constraints**: Ensures that an execution trade cannot exist without a valid parent order, which cannot exist without a valid stock and paper account.
* **Numeric Precision (`NUMERIC` / `DECIMAL`)**: Floating-point rounding errors are catastrophic in accounting. PostgreSQL supports arbitrary-precision `NUMERIC(15, 4)` and `NUMERIC(12, 2)` types, preventing IEEE-754 float drift.
* **Time-Series Extensibility**: TimescaleDB extension can be layered directly on PostgreSQL when scaling from daily bars to millisecond tick data, avoiding a premature migration to specialized databases.

*(Note: SQLite is supported seamlessly in development via SQLAlchemy ORM abstractions).*

---

## 3. Why Pandas?
* **High-Performance Vectorized Computations**: Calculating technical indicators (EMA, RSI, Rolling Standard Deviations, Volatility) over thousands of historical bars in Python loops is slow (`O(N)` with Python interpreter overhead). Pandas leverages C-optimized NumPy arrays to compute rolling statistics vectorially in milliseconds.
* **Time-Series Indexing & Alignment**: Automatic handling of calendar dates, market holidays, timezones (`Asia/Kolkata`), date slicing, and missing data imputation (`ffill`, `bfill`).
* **Interoperability**: Standard lingua franca of financial engineering, data science, and quantitative libraries (NumPy, SciPy, Ta-Lib, Backtrader).

---

## 4. Why Next.js (App Router, TypeScript, Tailwind CSS)?
* **Component-Driven Modular Architecture**: Complex trading interfaces require independent, self-contained widgets (interactive charts, order entry forms, portfolio summaries, real-time audit logs).
* **Compile-Time Type Safety**: TypeScript enforces strict contracts matching backend Pydantic models. Any field mismatch (e.g., `realized_pnl` vs `realised_profit`) is caught at build time.
* **Responsive Visual Feedback**: Tailwind CSS enables building high-density, low-latency, responsive dark-mode dashboards reminiscent of Bloomberg Terminal and TradingView.
* **Separation of Concerns**: Static and client-rendered components decouple presentation state from server business logic.

---

## 5. Why EMA instead of only SMA?
* **Weighting Mechanism**:
  $$\text{SMA}_t = \frac{1}{N} \sum_{i=0}^{N-1} P_{t-i}$$
  A Simple Moving Average (SMA) assigns equal weight ($1/N$) to all prices in the window. A price shock from $N$ days ago abruptly dropping off the window causes an artificial "jump" or phantom signal.
* **Exponential Decay**:
  $$\text{EMA}_t = \alpha \cdot P_t + (1 - \alpha) \cdot \text{EMA}_{t-1}, \quad \text{where } \alpha = \frac{2}{N + 1}$$
  An Exponential Moving Average (EMA) applies exponentially decreasing weights to older prices. It responds significantly faster to recent price momentum and trend reversals while smoothing out short-term market noise.

---

## 6. What is RSI (Relative Strength Index)?
* **Definition**: A bounded momentum oscillator ranging between $0$ and $100$, developed by J. Welles Wilder Jr., measuring the velocity and magnitude of directional price movements:
  $$\text{RSI} = 100 - \left( \frac{100}{1 + \text{RS}} \right), \quad \text{where } \text{RS} = \frac{\text{Average Gain}}{\text{Average Loss}}$$
* **Wilder's Smoothing**:
  $$\text{Avg Gain}_t = \frac{\text{Prior Avg Gain} \times (N-1) + \text{Current Gain}}{N}$$
* **Role in Strategy**: In our Fast EMA / Slow EMA trend-following strategy, RSI acts as a **momentum filter**. We only initiate long positions when $\text{RSI} > 50$ (bullish regime) and $\text{RSI} \le 85$ (avoiding parabolic blow-off exhaustion), exiting when $\text{RSI} < 45$.

---

## 7. What is OHLCV?
* **Core Bar Anatomy**:
  * **Open (O)**: The price at which the asset first traded during the bar interval (09:15 IST for daily bars).
  * **High (H)**: The absolute maximum price reached during the interval.
  * **Low (L)**: The absolute minimum price reached during the interval.
  * **Close (C)**: The final traded price when the interval ended (15:30 IST for NSE daily bars).
  * **Volume (V)**: The aggregate number of shares transacted throughout the interval.
* **Importance**: OHLCV bars capture intra-period volatility, price range, liquidity, and conviction without requiring continuous tick-by-tick storage.

---

## 8. What is Paper Trading?
* **Simulated Execution**: Running an algorithmic strategy against real or simulated market data where orders are executed against an in-memory or database-backed simulated brokerage ledger rather than routing to live exchange order books (NSE/BSE).
* **Purpose**:
  1. Validates real-time order generation logic and state transitions without capital risk.
  2. Surfaces race conditions, rounding errors, and position-tracking bugs.
  3. Tests psychological and execution workflows before deploying capital.
* **Implementation in TradeBot**: Maintains a dedicated `paper_accounts` ledger with strict cash deductions, position tracking, average entry price recalculations, and simulated regulatory fees.

---

## 9. What is Backtesting?
* **Historical Simulation**: Evaluating how a quantitative trading strategy would have performed over historical market periods by simulating candle-by-candle market conditions.
* **Key Deliverables**:
  * Compounded Total Return vs. Benchmark (Buy & Hold).
  * Maximum Drawdown (MDD) & Drawdown Duration.
  * Win Rate & Profit Factor ($\sum \text{Gains} / \sum \text{Losses}$).
  * Total Transaction Costs & Slippage Impact.

---

## 10. What is Look-Ahead Bias & How is it Prevented?
* **Look-Ahead Bias**: The fatal flaw in backtesting where calculations or decisions at bar $t$ inadvertently access data from bar $t+1$ or later (or access bar $t$'s Close to trade at bar $t$'s Open). In real life, tomorrow's price is unknown today.
* **How TradeBot Enforces Zero Look-Ahead Bias**:
  1. **$t+1$ Open Execution Rule**: When indicators on bar $t$ satisfy entry/exit criteria at the Close of bar $t$, the trade is strictly executed on **bar $t+1$ at the Open price**.
  2. **Intrabar Conservative Priority**: When evaluating Stop-Loss and Take-Profit within bar $k$, if both price thresholds are breached within the same bar's $[Low, High]$ range, the backtest engine **prioritizes the Stop-Loss first**, modeling the worst-case scenario.

---

## 11. How is P&L Calculated?
* **Unrealized P&L** (Open Positions):
  $$\text{Unrealized P\&L} = (\text{Current Market Price} - \text{Average Entry Price}) \times \text{Quantity}$$
* **Gross Realized P&L** (Closed Positions):
  $$\text{Gross Realized P\&L} = (\text{Exit Price} - \text{Average Entry Price}) \times \text{Closed Quantity}$$
* **Net Realized P&L** (After Friction):
  $$\text{Net Realized P\&L} = \text{Gross Realized P\&L} - \text{Entry Fees} - \text{Exit Fees} - \text{Slippage}$$
* **Portfolio Total Equity**:
  $$\text{Total Equity} = \text{Cash Balance} + \sum (\text{Market Value of All Open Positions})$$

---

## 12. How are Indian Equity Transaction Costs Handled?
TradeBot implements a realistic, statutory Indian Cash Delivery regulatory cost model:
1. **Securities Transaction Tax (STT)**: 0.1% on both Buy and Sell turnover.
2. **Exchange Turnover Charges (NSE)**: 0.00325% of turnover.
3. **SEBI Turnover Charges**: ₹10 per crore (0.0001%).
4. **GST**: 18% levied on (Brokerage + Exchange Charges + SEBI Charges).
5. **Stamp Duty**: 0.015% on Buy turnover only.
6. **Execution Slippage**: 0.05% price penalty on market fills.

---

## 13. How does the System Prevent Overselling?
* **Validation at Risk Layer**:
  When a SELL order arrives, `RiskManager.validate_order()` verifies:
  1. Does an open position for this symbol exist?
  2. Is `order.quantity <= position.quantity`?
* **Atomicity & Locking**:
  Orders exceeding current inventory are rejected with HTTP 400 (`INSUFFICIENT_POSITION`). No naked short selling is permitted in this cash equity system.

---

## 14. How is Market Data Cached?
* **Two-Tier Storage**:
  1. In-Memory caching of recently evaluated indicator frames.
  2. Persistent Relational Database (`market_data` table) keyed by `(stock_id, timestamp)` with a unique constraint.
* **Conditional Ingestion**:
  Before making outbound network calls to upstream data providers, TradeBot checks the database for existing bars. Only missing or requested fresh bars are ingested and merged using idempotent `ON CONFLICT DO NOTHING` operations.

---

## 15. How does the Strategy Remain Independent of the API?
* **Clean Architecture & Separation of Concerns**:
  * `Strategy` classes inherit from `BaseStrategy` and accept standard Pandas DataFrames, returning pure domain `Signal` objects (`BUY`, `SELL`, `HOLD`).
  * Strategies have zero dependencies on FastAPI, HTTP requests, or database sessions.
  * Any strategy can be executed via CLI, Jupyter notebook, backtesting engine, or API endpoint without modifying a single line of code.

---

## 16. How would a Real Broker API be Integrated in the Future?
* **Broker Adapter Interface Pattern**:
  ```python
  class BrokerAdapter(ABC):
      @abstractmethod
      async def place_order(self, order: OrderRequest) -> OrderResponse: ...
      @abstractmethod
      async def cancel_order(self, broker_order_id: str) -> bool: ...
      @abstractmethod
      async def get_account_balance(self) -> AccountBalance: ...
      @abstractmethod
      async def get_positions(self) -> List[Position]: ...
  ```
* **Pluggable Architecture**:
  To connect Zerodha Kite Connect, Angel One SmartAPI, or Upstox, implement `KiteBrokerAdapter(BrokerAdapter)` and inject it into the execution layer. The paper trading engine is simply `PaperBrokerAdapter`.

---

## 17. What are the Limitations of the Data Source?
* **Yahoo Finance (`yfinance`)**:
  * Free, unauthenticated tier suitable for research, education, and offline development.
  * Data is delayed ~15 minutes during live market hours.
  * Subject to upstream rate limits, schema changes, and potential missing corporate actions (splits/dividends).
  * **Transparency**: The UI and API clearly label data feeds as `Historical`, `Latest Available (Delayed)`, or `Simulated`.

---

## 18. Why don't Backtest Results Guarantee Future Performance?
* **Regime Shifts**: Market dynamics change due to macroeconomic factors, interest rate cycles, and geopolitical events. Past trend persistence may fail in choppy, mean-reverting regimes.
* **Overfitting / Curve-Fitting**: Optimizing parameters (e.g., test 100 EMA combinations to find the highest return) captures past noise rather than genuine predictive signal.
* **Market Impact & Liquidity**: Simulated backtests assume infinite liquidity at quoted prices; in real markets, large orders shift the order book and incur adverse selection.
* **Survivor Bias**: Backtesting only on currently surviving index constituents ignores companies that were delisted or went bankrupt.
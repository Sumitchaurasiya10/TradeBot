# System Architecture: Indian Equity Market Paper Trading Bot

## 1. High-Level Architectural Flow

`
[ Data Provider Abstraction ]
  ├── YFinanceProvider (Development/Educational)
  └── [Future: KiteConnectProvider / AngelOneProvider]
                │
                ▼
     [ Data Normalizer & Validator ]
     (Enforces OHLC relationships, drops duplicates, enforces IST/UTC)
                │
                ▼
      [ Database Caching Layer ] ◄── (Idempotent: unique (stock_id, timestamp))
                │
                ▼
     [ Technical Indicators Engine ]
     (Vectorized EMA, RSI, Volume MA calculations; pure Pandas)
                │
                ▼
       [ Strategy Engine: EMARsiVolumeStrategy ]
       (Accepts DataFrame -> Returns Structured Signal: BUY / SELL / HOLD)
                │
        ┌───────┴────────────────────────┐
        ▼                                ▼
[ Backtesting Engine ]          [ Risk Management ]
- Chronological bar-by-bar      - Max allocation % per trade
- Signal at t -> Exec at t+1 Open- Stop-loss % & Take-profit %
- Intrabar SL/TP conservative    - Max open positions
- Transaction cost model                 │
- Benchmark: Buy-and-Hold                ▼
- Zero look-ahead leakage tests [ Paper Trading Engine ]
                                - Single account ledger (MVP)
                                - Decimal arithmetic (no float rounding)
                                - Cash & Position state
                                - Order validation (no overselling)
                                         │
                                         ▼
                             [ Database: PostgreSQL / SQLite ]
                                         │
                                         ▼
                               [ FastAPI REST API (/api/v1) ]
                                         │
                                         ▼
                            [ Next.js 14 Dashboard ]
                            (Labels: Historical / Delayed / Simulated)
`

## 2. Decoupling & Clean Architecture Principles

1. **Framework Independence**:
   - strategies/, services/indicators.py, and acktesting/ are pure Python modules operating on standard Pandas DataFrames.
   - They have **zero dependencies** on FastAPI, HTTP frameworks, or SQLAlchemy database models.
   - This ensures unit tests can run offline with deterministic data in milliseconds without needing network or database access.

2. **Data Provider Abstraction**:
   - Market data is accessed via a generic DataProvider interface.
   - The initial implementation uses YFinanceProvider (fetching NSE .NS tickers).
   - If an official broker API (e.g. Zerodha Kite Connect) is integrated later, only a new subclass of DataProvider is required; no core trading or backtesting logic changes.

3. **Execution Timing & Look-Ahead Bias Prevention**:
   - Signal calculated on Candle $ Close is executed at Candle +1$ **Open**.
   - Intrabar Stop-Loss / Take-Profit rule assumes conservative Stop-Loss execution if both levels are touched within the candle range.

4. **Accounting Precision**:
   - All cash, balance, and P&L calculations use Python Decimal and SQLAlchemy Numeric(14, 4) / Numeric(14, 2) to eliminate floating-point rounding errors.

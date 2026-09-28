# System Architecture: Indian Equity & Derivatives Paper Trading Bot

## 1. High-Level Architectural Flow

```
[ Market Data Provider Abstraction ]
  ├── HistoricalMarketDataProvider (Fast Yahoo Finance NSE Quotes & Indices)
  ├── MockLiveMarketDataProvider (Simulated Live Streaming + Black-Scholes F&O Option Chains)
  └── [Future: KiteConnectLiveProvider / SmartAPILiveProvider]
                │
                ▼
     [ Live Market Cache & Staleness Engine ]
     (In-Memory TTL tracking: >60s flags DataStatus.STALE)
                │
         ┌──────┴─────────────────────────────────┐
         ▼                                        ▼
[ Market Session Service ]             [ WebSocket Tick Stream ]
- Asia/Kolkata Schedule                - Full-Duplex /ws/market
- Pre-Open: 09:00 - 09:15              - Client Subscriptions
- Market Open: 09:15 - 15:30                      │
- Post-Market: 15:30 - 16:00                      ▼
- Market Closed                        [ Tick-to-Candle Aggregator ]
                                       - 1m, 5m, 15m, 1D OHLCV Bars
                │
                ▼
[ F&O Derivatives Engine ]
- Real-time Option Chains (CE / PE)
- Strike Ladder with ATM detection
- Black-Scholes Pricing & Implied Volatility
- Open Interest (OI) & OI Change
                │
                ▼
[ Strategy Engine: EMARsiVolumeStrategy ]
- Fast EMA (9) + Slow EMA (21) Crossover
- RSI (14) Momentum filter
- Volume Moving Average (20) filter
- Real-time Live Signal Bridge (`/strategy/live-signal/{symbol}`)
                │
        ┌───────┴────────────────────────┐
        ▼                                ▼
[ Backtesting Engine ]          [ Risk Management ]
- Chronological bar-by-bar      - Max allocation % per trade (10%)
- Signal at t -> Exec at t+1 Open- Stop-loss % & Take-profit %
- Intrabar SL/TP conservative    - Max open positions
- Transaction cost model                 │
- Benchmark: Buy-and-Hold                ▼
- Zero look-ahead leakage tests [ Paper Trading Engine ]
                                - Single account ledger
                                - Decimal arithmetic (no float rounding)
                                - Cash & Position state
                                - Market order fill at live LTP
                                - Dynamic unrealized P&L updates
                                         │
                                         ▼
                             [ Database: PostgreSQL / SQLite ]
                                         │
                                         ▼
                               [ FastAPI Gateway (/api/v1) ]
                                         │
                                         ▼
                            [ Next.js 14 Dashboard ]
                            (Labels: LIVE / DELAYED / HISTORICAL / DEMO DATA)
```

## 2. Decoupling & Clean Architecture Principles

1. **Market Data Provider Abstraction (`MarketDataProvider`)**:
   - Trading, backtesting, strategy evaluation, and UI display are completely decoupled from external market data APIs.
   - All components interact exclusively through the abstract `MarketDataProvider` contract.
   - `MockLiveMarketDataProvider` generates high-fidelity Indian market ticks and Black-Scholes options pricing tagged `DEMO DATA` / `SIMULATED`, allowing development and testing outside trading hours without real broker credentials.
   - `HistoricalMarketDataProvider` ingests fast daily snapshots and historical series from NSE (`.NS` tickers) and BSE.
   - Pluggable design enables dropping in production broker APIs (Zerodha Kite Connect or Angel One SmartAPI) with zero changes to business logic.

2. **Data Transparency & Staleness Tracking**:
   - Every single quote, index, and contract explicitly carries a `DataStatus`:
     - `LIVE`: Verified real-time streaming feed.
     - `DELAYED`: Exchange delayed feed (typically 15 minutes).
     - `HISTORICAL`: End-of-day official exchange settlement data.
     - `DEMO DATA` / `SIMULATED`: Synthetic ticks or Black-Scholes pricing.
     - `STALE`: Cached data exceeding 60 seconds of age.
     - `UNAVAILABLE`: Feed offline or market closed.
   - The UI displays explicit color-coded status badges on every instrument.

3. **Session Awareness & Timezone Handling**:
   - Operates strictly in the `Asia/Kolkata` (IST) timezone.
   - Real-time trading session transitions:
     - `PRE-OPEN`: 09:00 to 09:15 IST
     - `MARKET OPEN`: 09:15 to 15:30 IST
     - `POST-MARKET`: 15:30 to 16:00 IST
     - `MARKET CLOSED`: Evenings, nights, and weekends

4. **Framework Independence & Offline Testability**:
   - `strategies/`, `services/indicators.py`, `services/candle_builder.py`, and `backtesting/` are pure Python modules operating on standard Pandas DataFrames and Python primitives.
   - Zero dependencies on FastAPI, HTTP frameworks, or external network connections for unit tests.
   - Complete 73-test Pytest test suite runs 100% offline in under 4 seconds.

5. **Execution Timing & Look-Ahead Bias Prevention**:
   - Signal calculated on Candle $t$'s Close is executed at Candle $t+1$'s **Open**.
   - Intrabar Stop-Loss / Take-Profit rule assumes conservative Stop-Loss execution if both levels are touched within the candle range.

6. **Strict Accounting Precision**:
   - All cash, balance, order values, and P&L calculations use Python `Decimal` and SQLAlchemy `Numeric(14, 4)` / `Numeric(14, 2)` to eliminate floating-point rounding errors.
   - Indian transaction cost model includes STT, Exchange turnover, SEBI charges, GST, and stamp duty.

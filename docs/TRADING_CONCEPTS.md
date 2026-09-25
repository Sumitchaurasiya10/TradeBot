# Trading Concepts & Mathematical Foundations

## 1. Indian Stock Market Mechanics

* **Exchange**: National Stock Exchange (NSE). Equities are tagged with .NS (e.g., RELIANCE.NS, TCS.NS, INFY.NS, HDFCBANK.NS, ICICIBANK.NS).
* **Trading Hours**: Monday to Friday, **09:15 AM to 03:30 PM IST** (Timezone: Asia/Kolkata).
* **Cash Delivery (CNC) vs Intraday**:
  * Retail cash equity cannot be shorted overnight under SEBI regulations.
  * Our bot strictly implements **Long-Only Cash Trading** (Buy to Open, Sell to Close).

## 2. Market Data: OHLCV

* **Open ($)**: First traded price in the interval.
* **High ($)**: Maximum traded price in the interval.
* **Low ($)**: Minimum traded price in the interval.
* **Close ($)**: Final traded price in the interval.
* **Volume ($)**: Total shares transacted.
* **Data Validation Invariants**:
  1.  \ge Open$ and  \ge Close$
  2.  \le Open$ and  \le Close$
  3.  \ge 0$

## 3. Mathematical Indicator Formulas

### A. Exponential Moving Average (EMA)
The recursive formula is:
\alpha = \frac{2}{N + 1}
\text{EMA}_t = \alpha \times \text{Close}_t + (1 - \alpha) \times \text{EMA}_{t-1}
Where $ is the period (e.g., =9$ for Fast EMA, =21$ for Slow EMA).

### B. Relative Strength Index (RSI)
RSI measures momentum on a $ to $ scale over $ periods (default =14$):
\text{RS} = \frac{\text{Average Gain}}{\text{Average Loss}}
\text{RSI} = 100 - \frac{100}{1 + \text{RS}}
*Note*: 30 and 70 are historical reference levels, not universal buy/sell rules. The strategy explicitly sets its entry/exit thresholds.

### C. Volume Filter
\text{Volume MA}_{20} = \frac{1}{20} \sum_{i=0}^{19} \text{Volume}_{t-i}
Breakout confirmation requires $\text{Volume}_t > (\text{Volume MA}_{20} \times \text{Multiplier})$.

## 4. Backtesting & Execution Timing

* **Signal at $**: Evaluated after candle $ closes.
* **Execution at +1$ Open**: Simulated trade fills at candle +1$ Open price with transaction costs and slippage.
* **Look-Ahead Bias**: Prevented by never passing future indices to indicator or signal generators.
* **Benchmark**: Buy-and-Hold return over the same period displayed for transparent comparison.

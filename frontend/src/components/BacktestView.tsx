"use client";

import React, { useState } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { ArrowDownRight, ArrowUpRight, BarChart3, Clock, DollarSign, Play, ShieldAlert, TrendingUp } from "lucide-react";
import { api } from "../services/api";
import { BacktestResponse, Stock } from "../types";

interface BacktestViewProps {
  stocks: Stock[];
}

export const BacktestView: React.FC<BacktestViewProps> = ({ stocks }) => {
  const [symbol, setSymbol] = useState("TCS.NS");
  const [initialCapital, setInitialCapital] = useState(100000);
  const [fastEma, setFastEma] = useState(9);
  const [slowEma, setSlowEma] = useState(21);
  const [rsiPeriod, setRsiPeriod] = useState(14);
  const [rsiEntryThreshold, setRsiEntryThreshold] = useState(50.0);
  const [rsiExitThreshold, setRsiExitThreshold] = useState(45.0);
  const [volumeMultiplier, setVolumeMultiplier] = useState(1.0);
  const [stopLossPct, setStopLossPct] = useState(0.02);
  const [takeProfitPct, setTakeProfitPct] = useState(0.05);
  const [positionSizePct, setPositionSizePct] = useState(0.20);

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<BacktestResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleRunBacktest = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.runBacktest({
        symbol,
        initial_capital: initialCapital,
        fast_ema_period: fastEma,
        slow_ema_period: slowEma,
        rsi_period: rsiPeriod,
        rsi_entry_threshold: rsiEntryThreshold,
        rsi_max_threshold: 85.0,
        rsi_exit_threshold: rsiExitThreshold,
        volume_ma_period: 20,
        volume_multiplier: volumeMultiplier,
        stop_loss_pct: stopLossPct,
        take_profit_pct: takeProfitPct,
        position_size_pct: positionSizePct,
      });
      setResult(res);
    } catch (err: any) {
      setError(err.message || "Backtest execution failed");
    } finally {
      setLoading(false);
    }
  };

  const chartData = (result?.equity_curve || []).map((pt) => ({
    date: pt.timestamp.split("T")[0],
    equity: pt.equity,
    drawdown: pt.drawdown_pct,
  }));

  const beatBenchmark = result ? result.total_return_pct >= result.benchmark_return_pct : false;

  return (
    <div className="space-y-6">
      {/* Parameter Inputs Panel */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 backdrop-blur">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border-b border-slate-800/80 pb-4">
          <div>
            <div className="flex items-center space-x-2">
              <BarChart3 className="h-5 w-5 text-emerald-400" />
              <h2 className="text-lg font-bold text-white tracking-tight">Historical Backtesting Lab</h2>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Strict chronological simulation (Candle $t$ Signal &rarr; Candle $t+1$ Open Fill) with transaction costs
            </p>
          </div>

          <button
            onClick={handleRunBacktest}
            disabled={loading}
            className="flex items-center space-x-2 px-6 py-2.5 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-semibold text-sm rounded-lg transition shadow-lg shadow-emerald-950/40"
          >
            <Play className={`h-4 w-4 ${loading ? "animate-spin" : "fill-current"}`} />
            <span>{loading ? "Running Simulation..." : "Run Backtest"}</span>
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-6">
          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1">Target Stock</label>
            <select
              value={symbol}
              onChange={(e) => setSymbol(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-emerald-500"
            >
              {stocks.map((s) => (
                <option key={s.symbol} value={s.symbol}>
                  {s.symbol}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1">Initial Capital (₹)</label>
            <input
              type="number"
              value={initialCapital}
              onChange={(e) => setInitialCapital(Number(e.target.value))}
              min={1000}
              className="w-full bg-slate-950 border border-slate-700 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-emerald-500"
            />
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1">Fast EMA / Slow EMA</label>
            <div className="flex space-x-2">
              <input
                type="number"
                value={fastEma}
                onChange={(e) => setFastEma(Number(e.target.value))}
                className="w-1/2 bg-slate-950 border border-slate-700 text-white rounded-lg px-2 py-2 text-sm"
              />
              <input
                type="number"
                value={slowEma}
                onChange={(e) => setSlowEma(Number(e.target.value))}
                className="w-1/2 bg-slate-950 border border-slate-700 text-white rounded-lg px-2 py-2 text-sm"
              />
            </div>
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1">RSI Entry / Exit Thresholds</label>
            <div className="flex space-x-2">
              <input
                type="number"
                value={rsiEntryThreshold}
                onChange={(e) => setRsiEntryThreshold(Number(e.target.value))}
                className="w-1/2 bg-slate-950 border border-slate-700 text-white rounded-lg px-2 py-2 text-sm"
              />
              <input
                type="number"
                value={rsiExitThreshold}
                onChange={(e) => setRsiExitThreshold(Number(e.target.value))}
                className="w-1/2 bg-slate-950 border border-slate-700 text-white rounded-lg px-2 py-2 text-sm"
              />
            </div>
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1">Stop-Loss % (Default 2%)</label>
            <input
              type="number"
              step="0.005"
              value={stopLossPct}
              onChange={(e) => setStopLossPct(Number(e.target.value))}
              className="w-full bg-slate-950 border border-slate-700 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-emerald-500"
            />
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1">Take-Profit % (Default 5%)</label>
            <input
              type="number"
              step="0.005"
              value={takeProfitPct}
              onChange={(e) => setTakeProfitPct(Number(e.target.value))}
              className="w-full bg-slate-950 border border-slate-700 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-emerald-500"
            />
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1">Position Size (% of Capital)</label>
            <input
              type="number"
              step="0.05"
              value={positionSizePct}
              onChange={(e) => setPositionSizePct(Number(e.target.value))}
              className="w-full bg-slate-950 border border-slate-700 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-emerald-500"
            />
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1">Volume Multiplier</label>
            <input
              type="number"
              step="0.1"
              value={volumeMultiplier}
              onChange={(e) => setVolumeMultiplier(Number(e.target.value))}
              className="w-full bg-slate-950 border border-slate-700 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-emerald-500"
            />
          </div>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-lg text-rose-400 text-sm">
          {error}
        </div>
      )}

      {/* Backtest Results */}
      {result && (
        <div className="space-y-6">
          {/* Strategy vs Benchmark Comparison Card */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 backdrop-blur">
            <h3 className="text-base font-bold text-white mb-4">Performance vs Buy-and-Hold Benchmark</h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Strategy Card */}
              <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-5">
                <div className="flex justify-between items-center text-xs text-slate-400">
                  <span>STRATEGY RETURN</span>
                  <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 text-[10px] font-bold">
                    EMA + RSI + VOLUME
                  </span>
                </div>
                <div className={`text-3xl font-extrabold mt-2 ${result.total_return_pct >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                  {result.total_return_pct >= 0 ? "+" : ""}{result.total_return_pct.toFixed(2)}%
                </div>
                <div className="text-sm font-semibold text-slate-200 mt-1">
                  Final Equity: ₹{result.final_equity.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                </div>
              </div>

              {/* Benchmark Card */}
              <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-5">
                <div className="flex justify-between items-center text-xs text-slate-400">
                  <span>BUY & HOLD BENCHMARK</span>
                  <span className="px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 text-[10px] font-bold">
                    PASSIVE HOLDING
                  </span>
                </div>
                <div className={`text-3xl font-extrabold mt-2 ${result.benchmark_return_pct >= 0 ? "text-blue-400" : "text-rose-400"}`}>
                  {result.benchmark_return_pct >= 0 ? "+" : ""}{result.benchmark_return_pct.toFixed(2)}%
                </div>
                <div className="text-sm font-semibold text-slate-400 mt-1">
                  Underlying {result.symbol} price action
                </div>
              </div>
            </div>

            {/* Detailed Metric Badges */}
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mt-4">
              <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800">
                <span className="text-[11px] text-slate-400">Total Trades</span>
                <div className="text-base font-bold text-white">{result.total_trades}</div>
              </div>
              <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800">
                <span className="text-[11px] text-slate-400">Win Rate</span>
                <div className="text-base font-bold text-emerald-400">{result.win_rate_pct.toFixed(1)}%</div>
              </div>
              <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800">
                <span className="text-[11px] text-slate-400">Max Drawdown</span>
                <div className="text-base font-bold text-rose-400">{result.max_drawdown_pct.toFixed(2)}%</div>
              </div>
              <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800">
                <span className="text-[11px] text-slate-400">Profit Factor</span>
                <div className="text-base font-bold text-white">{result.profit_factor >= 999 ? "∞" : result.profit_factor.toFixed(2)}</div>
              </div>
              <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800">
                <span className="text-[11px] text-slate-400">Avg Trade Return</span>
                <div className="text-base font-bold text-slate-200">{result.average_trade_return_pct.toFixed(2)}%</div>
              </div>
              <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800">
                <span className="text-[11px] text-slate-400">Total Fees</span>
                <div className="text-base font-bold text-slate-400">₹{result.total_transaction_costs.toFixed(2)}</div>
              </div>
            </div>
          </div>

          {/* Equity Curve Chart */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 backdrop-blur">
            <h3 className="font-bold text-white text-sm sm:text-base mb-4">Simulated Portfolio Equity Curve (₹)</h3>
            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="date" stroke="#64748b" tick={{ fontSize: 11 }} />
                  <YAxis
                    stroke="#64748b"
                    domain={["auto", "auto"]}
                    tick={{ fontSize: 11 }}
                    tickFormatter={(v) => `₹${Number(v).toFixed(0)}`}
                  />
                  <Tooltip
                    contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155", borderRadius: 8, fontSize: 12 }}
                    formatter={(val: any) => [`₹${Number(val).toLocaleString("en-IN", { minimumFractionDigits: 2 })}`, "Equity"]}
                  />
                  <Line type="monotone" dataKey="equity" stroke="#10b981" strokeWidth={2} dot={false} name="Equity" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Trade-by-Trade Table */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 backdrop-blur">
            <h3 className="font-bold text-white text-base mb-4">Trade-by-Trade Execution Log ({result.trades.length})</h3>
            {result.trades.length === 0 ? (
              <div className="text-center py-6 text-slate-500 text-sm">
                No trades executed during this historical period with chosen parameters.
              </div>
            ) : (
              <div className="overflow-x-auto max-h-96">
                <table className="w-full text-left text-sm text-slate-300">
                  <thead className="bg-slate-950/80 text-xs uppercase text-slate-400 sticky top-0 border-b border-slate-800">
                    <tr>
                      <th className="py-2.5 px-3">#</th>
                      <th className="py-2.5 px-3">Entry Time</th>
                      <th className="py-2.5 px-3">Exit Time</th>
                      <th className="py-2.5 px-3">Entry (₹)</th>
                      <th className="py-2.5 px-3">Exit (₹)</th>
                      <th className="py-2.5 px-3">Qty</th>
                      <th className="py-2.5 px-3">Net P&L (₹)</th>
                      <th className="py-2.5 px-3">Return %</th>
                      <th className="py-2.5 px-3">Exit Reason</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {result.trades.map((t) => {
                      const isWin = t.net_pnl >= 0;
                      return (
                        <tr key={t.trade_id} className="hover:bg-slate-800/30">
                          <td className="py-2 px-3 text-slate-400">{t.trade_id}</td>
                          <td className="py-2 px-3 text-xs">{t.entry_timestamp.split("T")[0]}</td>
                          <td className="py-2 px-3 text-xs">{t.exit_timestamp.split("T")[0]}</td>
                          <td className="py-2 px-3">₹{t.entry_price.toFixed(2)}</td>
                          <td className="py-2 px-3">₹{t.exit_price.toFixed(2)}</td>
                          <td className="py-2 px-3">{t.quantity}</td>
                          <td className={`py-2 px-3 font-bold ${isWin ? "text-emerald-400" : "text-rose-400"}`}>
                            {isWin ? "+" : ""}₹{t.net_pnl.toFixed(2)}
                          </td>
                          <td className={`py-2 px-3 font-semibold ${isWin ? "text-emerald-400" : "text-rose-400"}`}>
                            {isWin ? "+" : ""}{t.return_pct.toFixed(2)}%
                          </td>
                          <td className="py-2 px-3 text-xs">
                            <span
                              className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                                t.exit_reason === "TAKE_PROFIT"
                                  ? "bg-emerald-500/10 text-emerald-400"
                                  : t.exit_reason === "STOP_LOSS"
                                  ? "bg-rose-500/10 text-rose-400"
                                  : "bg-blue-500/10 text-blue-400"
                              }`}
                            >
                              {t.exit_reason}
                            </span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

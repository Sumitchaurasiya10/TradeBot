"use client";

import React, { useState } from "react";
import { AlertCircle, CheckCircle2, ChevronRight, HelpCircle, Play, Sliders, TrendingUp, XCircle } from "lucide-react";
import { api } from "../services/api";
import { SignalResponse, Stock } from "../types";

interface StrategyViewProps {
  stocks: Stock[];
}

export const StrategyView: React.FC<StrategyViewProps> = ({ stocks }) => {
  const [symbol, setSymbol] = useState("TCS.NS");
  const [fastEma, setFastEma] = useState(9);
  const [slowEma, setSlowEma] = useState(21);
  const [rsiPeriod, setRsiPeriod] = useState(14);
  const [rsiEntryThreshold, setRsiEntryThreshold] = useState(50.0);
  const [rsiMaxThreshold, setRsiMaxThreshold] = useState(85.0);
  const [rsiExitThreshold, setRsiExitThreshold] = useState(45.0);
  const [volumeMaPeriod, setVolumeMaPeriod] = useState(20);
  const [volumeMultiplier, setVolumeMultiplier] = useState(1.0);

  const [loading, setLoading] = useState(false);
  const [signalResult, setSignalResult] = useState<SignalResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleEvaluate = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.evaluateSignal({
        symbol,
        fast_ema_period: fastEma,
        slow_ema_period: slowEma,
        rsi_period: rsiPeriod,
        rsi_entry_threshold: rsiEntryThreshold,
        rsi_max_threshold: rsiMaxThreshold,
        rsi_exit_threshold: rsiExitThreshold,
        volume_ma_period: volumeMaPeriod,
        volume_multiplier: volumeMultiplier,
      });
      setSignalResult(res);
    } catch (err: any) {
      setError(err.message || "Failed to evaluate signal");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Configuration Header */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 backdrop-blur">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border-b border-slate-800/80 pb-4">
          <div>
            <div className="flex items-center space-x-2">
              <Sliders className="h-5 w-5 text-emerald-400" />
              <h2 className="text-lg font-bold text-white tracking-tight">
                EMA Crossover + RSI + Volume Confirmation Strategy
              </h2>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Configurable, mathematically explainable rule-based momentum & trend strategy
            </p>
          </div>

          <button
            onClick={handleEvaluate}
            disabled={loading}
            className="flex items-center space-x-2 px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-semibold text-sm rounded-lg transition shadow-lg shadow-emerald-950/40"
          >
            <Play className={`h-4 w-4 ${loading ? "animate-spin" : "fill-current"}`} />
            <span>{loading ? "Evaluating..." : "Generate Signal"}</span>
          </button>
        </div>

        {/* Form Inputs Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-6">
          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1">Stock</label>
            <select
              value={symbol}
              onChange={(e) => setSymbol(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-emerald-500"
            >
              {stocks.map((s) => (
                <option key={s.symbol} value={s.symbol}>
                  {s.symbol} ({s.company_name})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1">Fast EMA Period (Default 9)</label>
            <input
              type="number"
              value={fastEma}
              onChange={(e) => setFastEma(Number(e.target.value))}
              min={2}
              max={50}
              className="w-full bg-slate-950 border border-slate-700 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-emerald-500"
            />
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1">Slow EMA Period (Default 21)</label>
            <input
              type="number"
              value={slowEma}
              onChange={(e) => setSlowEma(Number(e.target.value))}
              min={3}
              max={200}
              className="w-full bg-slate-950 border border-slate-700 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-emerald-500"
            />
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1">RSI Period (Default 14)</label>
            <input
              type="number"
              value={rsiPeriod}
              onChange={(e) => setRsiPeriod(Number(e.target.value))}
              min={2}
              max={50}
              className="w-full bg-slate-950 border border-slate-700 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-emerald-500"
            />
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1">RSI Bullish Entry (Default 50)</label>
            <input
              type="number"
              value={rsiEntryThreshold}
              onChange={(e) => setRsiEntryThreshold(Number(e.target.value))}
              className="w-full bg-slate-950 border border-slate-700 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-emerald-500"
            />
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1">RSI Bearish Exit (Default 45)</label>
            <input
              type="number"
              value={rsiExitThreshold}
              onChange={(e) => setRsiExitThreshold(Number(e.target.value))}
              className="w-full bg-slate-950 border border-slate-700 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-emerald-500"
            />
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1">Volume MA Period (Default 20)</label>
            <input
              type="number"
              value={volumeMaPeriod}
              onChange={(e) => setVolumeMaPeriod(Number(e.target.value))}
              className="w-full bg-slate-950 border border-slate-700 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-emerald-500"
            />
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1">Volume Multiplier (Default 1.0)</label>
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

      {/* Signal Output Display Card */}
      {signalResult && (
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 backdrop-blur space-y-6">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div>
              <span className="text-xs uppercase text-slate-400 font-semibold tracking-wider">EVALUATED SIGNAL FOR</span>
              <h3 className="text-2xl font-bold text-white mt-0.5">{signalResult.symbol}</h3>
              <p className="text-xs text-slate-400">Timestamp: {signalResult.timestamp}</p>
            </div>

            {/* Big Signal Badge */}
            <div>
              {signalResult.signal === "BUY" && (
                <div className="flex items-center space-x-2 px-6 py-3 rounded-xl bg-emerald-500/20 border-2 border-emerald-500 text-emerald-400 font-extrabold text-2xl tracking-wider shadow-lg shadow-emerald-950/50">
                  <CheckCircle2 className="h-7 w-7" />
                  <span>BUY</span>
                </div>
              )}
              {signalResult.signal === "SELL" && (
                <div className="flex items-center space-x-2 px-6 py-3 rounded-xl bg-rose-500/20 border-2 border-rose-500 text-rose-400 font-extrabold text-2xl tracking-wider shadow-lg shadow-rose-950/50">
                  <XCircle className="h-7 w-7" />
                  <span>SELL</span>
                </div>
              )}
              {signalResult.signal === "HOLD" && (
                <div className="flex items-center space-x-2 px-6 py-3 rounded-xl bg-amber-500/20 border-2 border-amber-500 text-amber-400 font-extrabold text-2xl tracking-wider shadow-lg shadow-amber-950/50">
                  <AlertCircle className="h-7 w-7" />
                  <span>HOLD</span>
                </div>
              )}
            </div>
          </div>

          {/* Reasoning Alert */}
          <div className="p-4 rounded-lg bg-slate-950/80 border border-slate-800">
            <span className="text-xs text-slate-400 uppercase font-semibold block mb-1">STRATEGY REASONING</span>
            <p className="text-sm font-medium text-slate-200">{signalResult.reason}</p>
          </div>

          {/* Snapshot Indicator Table */}
          <div>
            <span className="text-xs text-slate-400 uppercase font-semibold block mb-2">CALCULATED INDICATOR SNAPSHOT</span>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
              <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800">
                <span className="text-[11px] text-slate-400">Benchmark Close</span>
                <div className="text-base font-bold text-white">₹{signalResult.indicators.close?.toFixed(2) || "N/A"}</div>
              </div>
              <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800">
                <span className="text-[11px] text-slate-400">Fast EMA</span>
                <div className="text-base font-bold text-emerald-400">₹{signalResult.indicators.fast_ema?.toFixed(2) || "N/A"}</div>
              </div>
              <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800">
                <span className="text-[11px] text-slate-400">Slow EMA</span>
                <div className="text-base font-bold text-amber-400">₹{signalResult.indicators.slow_ema?.toFixed(2) || "N/A"}</div>
              </div>
              <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800">
                <span className="text-[11px] text-slate-400">RSI</span>
                <div className="text-base font-bold text-purple-400">{signalResult.indicators.rsi?.toFixed(2) || "N/A"}</div>
              </div>
              <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800">
                <span className="text-[11px] text-slate-400">Candle Volume</span>
                <div className="text-base font-bold text-slate-200">{signalResult.indicators.volume?.toLocaleString("en-IN") || "N/A"}</div>
              </div>
              <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800">
                <span className="text-[11px] text-slate-400">Volume MA (20)</span>
                <div className="text-base font-bold text-slate-200">{signalResult.indicators.volume_ma?.toLocaleString("en-IN") || "N/A"}</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Educational Rule Explanation Box */}
      <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-5 text-xs text-slate-300 space-y-2">
        <div className="flex items-center space-x-1.5 font-bold text-white text-sm">
          <HelpCircle className="h-4 w-4 text-emerald-400" />
          <span>How the Strategy Logic Works</span>
        </div>
        <ul className="list-disc list-inside space-y-1 text-slate-400">
          <li>
            <strong className="text-emerald-400">BUY Rule:</strong> Fast EMA crosses strictly above Slow EMA (<span className="text-slate-200">Fast EMA &gt; Slow EMA</span>) on candle $t$, with RSI &ge; entry threshold (default 50) and Volume &ge; Volume MA &times; multiplier.
          </li>
          <li>
            <strong className="text-rose-400">SELL Rule:</strong> Fast EMA crosses strictly below Slow EMA OR RSI drops below exit threshold (default 45).
          </li>
          <li>
            <strong className="text-amber-400">HOLD Rule:</strong> All other conditions where trend momentum is neutral or indicators are warming up.
          </li>
        </ul>
      </div>
    </div>
  );
};

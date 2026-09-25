"use client";

import React, { useEffect, useState } from "react";
import {
  Area,
  CartesianGrid,
  ComposedChart,
  Line,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Activity, BarChart2, RefreshCw, TrendingUp } from "lucide-react";
import { api } from "../services/api";
import { IndicatorDataPoint, IndicatorResponse, Stock } from "../types";

interface MarketViewProps {
  stocks: Stock[];
}

export const MarketView: React.FC<MarketViewProps> = ({ stocks }) => {
  const [selectedSymbol, setSelectedSymbol] = useState<string>("TCS.NS");
  const [indicatorData, setIndicatorData] = useState<IndicatorResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const loadData = async (symbol: string, force = false) => {
    try {
      if (force) setRefreshing(true);
      else setLoading(true);
      setError(null);

      if (force) {
        // Force refresh from provider
        await api.getMarketData(symbol, true);
      }
      const ind = await api.getIndicators(symbol, 9, 21, 14, 20);
      setIndicatorData(ind);
    } catch (err: any) {
      setError(err.message || "Failed to load market data");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    if (selectedSymbol) {
      loadData(selectedSymbol);
    }
  }, [selectedSymbol]);

  const bars = indicatorData?.bars || [];
  const latestBar = bars.length > 0 ? bars[bars.length - 1] : null;
  const prevBar = bars.length > 1 ? bars[bars.length - 2] : null;

  const priceChange = latestBar && prevBar ? latestBar.close - prevBar.close : 0;
  const priceChangePct = latestBar && prevBar ? (priceChange / prevBar.close) * 100 : 0;
  const isUp = priceChange >= 0;

  // Format data for Recharts (keep last 60 bars for readability)
  const chartBars = bars.slice(-60).map((b) => ({
    date: b.timestamp.split("T")[0],
    close: b.close,
    fast_ema: b.fast_ema,
    slow_ema: b.slow_ema,
    rsi: b.rsi,
    volume: b.volume,
    volume_ma: b.volume_ma,
  }));

  return (
    <div className="space-y-6">
      {/* Controls & Header */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 backdrop-blur flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div className="flex flex-wrap items-center gap-3">
          <label className="text-xs uppercase text-slate-400 font-semibold tracking-wider">Select Stock:</label>
          <select
            value={selectedSymbol}
            onChange={(e) => setSelectedSymbol(e.target.value)}
            className="bg-slate-950 border border-slate-700 text-white rounded-lg px-3 py-1.5 text-sm font-semibold focus:outline-none focus:border-emerald-500"
          >
            {stocks.map((s) => (
              <option key={s.symbol} value={s.symbol}>
                {s.symbol} - {s.company_name}
              </option>
            ))}
          </select>

          <span className="text-xs px-2.5 py-1 rounded bg-slate-800 text-slate-300 font-medium">
            Daily OHLCV Candles
          </span>
        </div>

        <button
          onClick={() => loadData(selectedSymbol, true)}
          disabled={loading || refreshing}
          className="flex items-center space-x-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-slate-200 text-xs font-semibold rounded-lg border border-slate-700 transition"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${refreshing ? "animate-spin text-emerald-400" : ""}`} />
          <span>{refreshing ? "Updating from Yahoo Finance..." : "Refresh Feed"}</span>
        </button>
      </div>

      {error && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-lg text-rose-400 text-sm">
          {error}
        </div>
      )}

      {/* Quote Summary Cards */}
      {latestBar && (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          <div className="bg-slate-900/60 border border-slate-800 rounded-lg p-3">
            <span className="text-[11px] text-slate-400 uppercase font-semibold">LATEST CLOSE</span>
            <div className="text-xl font-bold text-white mt-1">₹{latestBar.close.toFixed(2)}</div>
            <div className={`text-xs font-semibold mt-0.5 ${isUp ? "text-emerald-400" : "text-rose-400"}`}>
              {isUp ? "+" : ""}{priceChange.toFixed(2)} ({isUp ? "+" : ""}{priceChangePct.toFixed(2)}%)
            </div>
          </div>

          <div className="bg-slate-900/60 border border-slate-800 rounded-lg p-3">
            <span className="text-[11px] text-slate-400 uppercase font-semibold">OPEN / HIGH</span>
            <div className="text-sm font-semibold text-slate-200 mt-1">O: ₹{latestBar.open.toFixed(2)}</div>
            <div className="text-sm font-semibold text-slate-200">H: ₹{latestBar.high.toFixed(2)}</div>
          </div>

          <div className="bg-slate-900/60 border border-slate-800 rounded-lg p-3">
            <span className="text-[11px] text-slate-400 uppercase font-semibold">LOW / VOLUME</span>
            <div className="text-sm font-semibold text-slate-200 mt-1">L: ₹{latestBar.low.toFixed(2)}</div>
            <div className="text-xs text-slate-400">Vol: {latestBar.volume.toLocaleString("en-IN")}</div>
          </div>

          <div className="bg-slate-900/60 border border-slate-800 rounded-lg p-3">
            <span className="text-[11px] text-slate-400 uppercase font-semibold">FAST EMA (9)</span>
            <div className="text-lg font-bold text-emerald-400 mt-1">
              {latestBar.fast_ema ? `₹${latestBar.fast_ema.toFixed(2)}` : "Warming up"}
            </div>
            <div className="text-[11px] text-slate-500">Short-term momentum</div>
          </div>

          <div className="bg-slate-900/60 border border-slate-800 rounded-lg p-3">
            <span className="text-[11px] text-slate-400 uppercase font-semibold">SLOW EMA (21)</span>
            <div className="text-lg font-bold text-amber-400 mt-1">
              {latestBar.slow_ema ? `₹${latestBar.slow_ema.toFixed(2)}` : "Warming up"}
            </div>
            <div className="text-[11px] text-slate-500">Baseline trend filter</div>
          </div>

          <div className="bg-slate-900/60 border border-slate-800 rounded-lg p-3">
            <span className="text-[11px] text-slate-400 uppercase font-semibold">RSI (14)</span>
            <div className="text-lg font-bold text-purple-400 mt-1">
              {latestBar.rsi ? latestBar.rsi.toFixed(2) : "Warming up"}
            </div>
            <div className="text-[11px] text-slate-500">
              {latestBar.rsi ? (latestBar.rsi > 70 ? "Overbought" : latestBar.rsi < 30 ? "Oversold" : "Neutral") : ""}
            </div>
          </div>
        </div>
      )}

      {/* Main Price & EMA Chart */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 backdrop-blur">
        <div className="flex justify-between items-center mb-4">
          <div className="flex items-center space-x-2">
            <TrendingUp className="h-5 w-5 text-emerald-400" />
            <h3 className="font-bold text-white text-sm sm:text-base">
              Price Action & EMA Crossover ({selectedSymbol})
            </h3>
          </div>
          <div className="flex items-center space-x-4 text-xs">
            <div className="flex items-center space-x-1">
              <span className="h-2 w-2 rounded-full bg-blue-400" />
              <span className="text-slate-300">Close</span>
            </div>
            <div className="flex items-center space-x-1">
              <span className="h-2 w-2 rounded-full bg-emerald-400" />
              <span className="text-slate-300">EMA 9</span>
            </div>
            <div className="flex items-center space-x-1">
              <span className="h-2 w-2 rounded-full bg-amber-400" />
              <span className="text-slate-300">EMA 21</span>
            </div>
          </div>
        </div>

        {loading ? (
          <div className="h-72 flex items-center justify-center text-slate-500 text-sm">
            Loading market chart...
          </div>
        ) : (
          <div className="h-80 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={chartBars} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="date" stroke="#64748b" tick={{ fontSize: 11 }} />
                <YAxis
                  stroke="#64748b"
                  domain={["auto", "auto"]}
                  tick={{ fontSize: 11 }}
                  tickFormatter={(val) => `₹${val}`}
                />
                <Tooltip
                  contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155", borderRadius: 8, fontSize: 12 }}
                  formatter={(value: any) => [`₹${Number(value).toFixed(2)}`, ""]}
                />
                <Area type="monotone" dataKey="close" stroke="#3b82f6" fillOpacity={0.1} fill="#3b82f6" name="Close" />
                <Line type="monotone" dataKey="fast_ema" stroke="#10b981" strokeWidth={1.5} dot={false} name="EMA 9" />
                <Line type="monotone" dataKey="slow_ema" stroke="#f59e0b" strokeWidth={1.5} dot={false} name="EMA 21" />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* Secondary RSI Chart */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 backdrop-blur">
        <div className="flex justify-between items-center mb-2">
          <div className="flex items-center space-x-2">
            <Activity className="h-5 w-5 text-purple-400" />
            <h3 className="font-bold text-white text-sm sm:text-base">Relative Strength Index (RSI 14)</h3>
          </div>
          <span className="text-xs text-slate-400">Reference: 30 (Oversold), 70 (Overbought)</span>
        </div>

        <div className="h-44 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={chartBars} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="date" stroke="#64748b" tick={{ fontSize: 11 }} />
              <YAxis stroke="#64748b" domain={[0, 100]} ticks={[0, 30, 50, 70, 100]} tick={{ fontSize: 11 }} />
              <Tooltip
                contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155", borderRadius: 8, fontSize: 12 }}
                formatter={(value: any) => [Number(value).toFixed(2), "RSI"]}
              />
              <ReferenceLine y={70} stroke="#ef4444" strokeDasharray="3 3" label={{ value: "70", fill: "#ef4444", fontSize: 10 }} />
              <ReferenceLine y={50} stroke="#64748b" strokeDasharray="2 2" />
              <ReferenceLine y={30} stroke="#10b981" strokeDasharray="3 3" label={{ value: "30", fill: "#10b981", fontSize: 10 }} />
              <Line type="monotone" dataKey="rsi" stroke="#c084fc" strokeWidth={1.8} dot={false} name="RSI 14" />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};

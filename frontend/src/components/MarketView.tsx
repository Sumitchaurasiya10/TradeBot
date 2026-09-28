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
import {
  Activity,
  ArrowDownRight,
  ArrowUpRight,
  BarChart2,
  Calendar,
  CheckCircle2,
  Clock,
  Layers,
  RefreshCw,
  TrendingDown,
  TrendingUp,
  Zap,
} from "lucide-react";
import { api } from "../services/api";
import { IndicatorResponse, Quote, SignalResponse, Stock } from "../types";

interface MarketViewProps {
  stocks: Stock[];
}

export const MarketView: React.FC<MarketViewProps> = ({ stocks }) => {
  const [selectedSymbol, setSelectedSymbol] = useState<string>("RELIANCE");
  const [timeframe, setTimeframe] = useState<string>("1M");
  const [indicatorData, setIndicatorData] = useState<IndicatorResponse | null>(null);
  const [liveQuote, setLiveQuote] = useState<Quote | null>(null);
  const [liveSignal, setLiveSignal] = useState<SignalResponse | null>(null);
  const [chartBars, setChartBars] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const timeframes = ["1D", "5D", "1M", "3M", "6M", "1Y"];

  const loadData = async (symbol: string, tf = timeframe, force = false) => {
    try {
      if (force) setRefreshing(true);
      else setLoading(true);
      setError(null);

      const clean = symbol.replace(".NS", "");

      // Parallel fetch: Quote, Indicators, Live Signal, and Multi-Timeframe Chart History
      const [quoteRes, indRes, signalRes, historyRes] = await Promise.allSettled([
        api.getQuote(clean, force),
        api.getIndicators(symbol, 9, 21, 14, 20),
        api.getLiveSignal(clean),
        api.getChartHistory(clean, tf),
      ]);

      if (quoteRes.status === "fulfilled") {
        setLiveQuote(quoteRes.value);
      }
      if (indRes.status === "fulfilled") {
        setIndicatorData(indRes.value);
      }
      if (signalRes.status === "fulfilled") {
        setLiveSignal(signalRes.value);
      }

      if (historyRes.status === "fulfilled" && historyRes.value?.bars?.length > 0) {
        const histBars = historyRes.value.bars;
        // Merge with indicator data if matching
        const indBarsMap = new Map((indRes.status === "fulfilled" ? indRes.value?.bars || [] : []).map((b) => [b.timestamp.split("T")[0], b]));
        const formatted = histBars.map((b: any) => {
          const dt = b.timestamp.split("T")[0];
          const ind = indBarsMap.get(dt);
          return {
            date: dt,
            close: b.close,
            open: b.open,
            high: b.high,
            low: b.low,
            volume: b.volume,
            fast_ema: ind?.fast_ema,
            slow_ema: ind?.slow_ema,
            rsi: ind?.rsi,
          };
        });
        setChartBars(formatted);
      } else if (indRes.status === "fulfilled" && indRes.value?.bars) {
        // Fallback to indicator bars (last 60)
        const formatted = indRes.value.bars.slice(-60).map((b) => ({
          date: b.timestamp.split("T")[0],
          close: b.close,
          open: b.open,
          high: b.high,
          low: b.low,
          fast_ema: b.fast_ema,
          slow_ema: b.slow_ema,
          rsi: b.rsi,
          volume: b.volume,
          volume_ma: b.volume_ma,
        }));
        setChartBars(formatted);
      }
    } catch (err: any) {
      setError(err.message || "Failed to load market data");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    if (selectedSymbol) {
      loadData(selectedSymbol, timeframe);
    }
  }, [selectedSymbol, timeframe]);

  const handleTimeframeChange = (tf: string) => {
    setTimeframe(tf);
    loadData(selectedSymbol, tf);
  };

  const ltp = liveQuote?.last_price || (chartBars.length > 0 ? chartBars[chartBars.length - 1].close : 0);
  const change = liveQuote?.change ?? 0;
  const changePct = liveQuote?.change_percent ?? 0;
  const isUp = change >= 0;

  const getStatusBadge = (status?: string) => {
    switch (status) {
      case "LIVE":
        return <span className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 px-2 py-0.5 rounded text-[10px] font-bold">● LIVE</span>;
      case "DELAYED":
        return <span className="bg-amber-500/10 text-amber-400 border border-amber-500/30 px-2 py-0.5 rounded text-[10px] font-bold">DELAYED (15m)</span>;
      case "HISTORICAL":
        return <span className="bg-blue-500/10 text-blue-400 border border-blue-500/30 px-2 py-0.5 rounded text-[10px] font-bold">HISTORICAL EOD</span>;
      case "DEMO DATA":
      case "SIMULATED":
        return <span className="bg-purple-500/10 text-purple-400 border border-purple-500/30 px-2 py-0.5 rounded text-[10px] font-bold">DEMO DATA</span>;
      default:
        return <span className="bg-slate-700 text-slate-300 px-2 py-0.5 rounded text-[10px] font-bold">{status || "STALE"}</span>;
    }
  };

  const getSignalBadge = (sig?: string) => {
    if (sig === "BUY") {
      return (
        <span className="flex items-center space-x-1 px-3 py-1 rounded-full text-xs font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/40">
          <ArrowUpRight className="h-3.5 w-3.5" />
          <span>BUY SIGNAL</span>
        </span>
      );
    }
    if (sig === "SELL") {
      return (
        <span className="flex items-center space-x-1 px-3 py-1 rounded-full text-xs font-bold bg-rose-500/20 text-rose-400 border border-rose-500/40">
          <ArrowDownRight className="h-3.5 w-3.5" />
          <span>SELL SIGNAL</span>
        </span>
      );
    }
    return (
      <span className="flex items-center space-x-1 px-3 py-1 rounded-full text-xs font-bold bg-slate-800 text-slate-300 border border-slate-700">
        <Clock className="h-3.5 w-3.5" />
        <span>NEUTRAL / HOLD</span>
      </span>
    );
  };

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
                {s.symbol.replace(".NS", "")} - {s.company_name}
              </option>
            ))}
          </select>

          {/* Timeframe Selector */}
          <div className="flex items-center space-x-1 bg-slate-950 border border-slate-800 rounded-lg p-0.5 overflow-x-auto max-w-full">
            {timeframes.map((tf) => (
              <button
                key={tf}
                onClick={() => handleTimeframeChange(tf)}
                className={`px-2.5 py-1 text-xs font-bold rounded transition ${
                  timeframe === tf
                    ? "bg-emerald-600 text-white shadow"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800"
                }`}
              >
                {tf}
              </button>
            ))}
          </div>
        </div>

        <div className="flex items-center space-x-3">
          {getStatusBadge(liveQuote?.data_status)}
          <button
            onClick={() => loadData(selectedSymbol, timeframe, true)}
            disabled={loading || refreshing}
            className="flex items-center space-x-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-slate-200 text-xs font-semibold rounded-lg border border-slate-700 transition"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${refreshing ? "animate-spin text-emerald-400" : ""}`} />
            <span>{refreshing ? "Fetching Live..." : "Refresh"}</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-lg text-rose-400 text-sm">
          {error}
        </div>
      )}

      {/* Quote Summary Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <div className="bg-slate-900/60 border border-slate-800 rounded-lg p-3">
          <span className="text-[11px] text-slate-400 uppercase font-semibold">LAST TRADED PRICE</span>
          <div className="text-xl font-bold font-mono text-white mt-1">₹{ltp.toFixed(2)}</div>
          <div className={`text-xs font-semibold mt-0.5 ${isUp ? "text-emerald-400" : "text-rose-400"}`}>
            {isUp ? "+" : ""}{change.toFixed(2)} ({isUp ? "+" : ""}{changePct.toFixed(2)}%)
          </div>
        </div>

        <div className="bg-slate-900/60 border border-slate-800 rounded-lg p-3">
          <span className="text-[11px] text-slate-400 uppercase font-semibold">DAY HIGH / LOW</span>
          <div className="text-xs font-semibold text-slate-200 mt-1">
            H: <span className="font-mono text-emerald-400">₹{(liveQuote?.high || 0).toFixed(2)}</span>
          </div>
          <div className="text-xs font-semibold text-slate-200 mt-0.5">
            L: <span className="font-mono text-rose-400">₹{(liveQuote?.low || 0).toFixed(2)}</span>
          </div>
        </div>

        <div className="bg-slate-900/60 border border-slate-800 rounded-lg p-3">
          <span className="text-[11px] text-slate-400 uppercase font-semibold">OPEN / PREV CLOSE</span>
          <div className="text-xs text-slate-200 mt-1">
            Open: <span className="font-mono font-semibold">₹{(liveQuote?.open || 0).toFixed(2)}</span>
          </div>
          <div className="text-xs text-slate-400 mt-0.5">
            Prev: <span className="font-mono">₹{(liveQuote?.previous_close || 0).toFixed(2)}</span>
          </div>
        </div>

        <div className="bg-slate-900/60 border border-slate-800 rounded-lg p-3">
          <span className="text-[11px] text-slate-400 uppercase font-semibold">FAST EMA (9)</span>
          <div className="text-lg font-bold font-mono text-emerald-400 mt-1">
            {liveSignal?.indicators?.fast_ema
              ? `₹${liveSignal.indicators.fast_ema.toFixed(2)}`
              : indicatorData?.bars?.slice(-1)[0]?.fast_ema
              ? `₹${indicatorData.bars.slice(-1)[0].fast_ema?.toFixed(2)}`
              : "—"}
          </div>
          <div className="text-[11px] text-slate-500">Short-term trend</div>
        </div>

        <div className="bg-slate-900/60 border border-slate-800 rounded-lg p-3">
          <span className="text-[11px] text-slate-400 uppercase font-semibold">SLOW EMA (21)</span>
          <div className="text-lg font-bold font-mono text-amber-400 mt-1">
            {liveSignal?.indicators?.slow_ema
              ? `₹${liveSignal.indicators.slow_ema.toFixed(2)}`
              : indicatorData?.bars?.slice(-1)[0]?.slow_ema
              ? `₹${indicatorData.bars.slice(-1)[0].slow_ema?.toFixed(2)}`
              : "—"}
          </div>
          <div className="text-[11px] text-slate-500">Baseline filter</div>
        </div>

        <div className="bg-slate-900/60 border border-slate-800 rounded-lg p-3">
          <span className="text-[11px] text-slate-400 uppercase font-semibold">RSI (14)</span>
          <div className="text-lg font-bold font-mono text-purple-400 mt-1">
            {liveSignal?.indicators?.rsi
              ? liveSignal.indicators.rsi.toFixed(2)
              : indicatorData?.bars?.slice(-1)[0]?.rsi
              ? indicatorData.bars.slice(-1)[0].rsi?.toFixed(2)
              : "—"}
          </div>
          <div className="text-[11px] text-slate-500">
            {liveSignal?.indicators?.rsi && liveSignal.indicators.rsi > 70
              ? "Overbought"
              : liveSignal?.indicators?.rsi && liveSignal.indicators.rsi < 30
              ? "Oversold"
              : "Neutral"}
          </div>
        </div>
      </div>

      {/* Live Strategy Signal Banner */}
      {liveSignal && (
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <Zap className="h-5 w-5 text-amber-400 shrink-0" />
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-xs uppercase font-bold text-slate-400">Live Strategy Signal:</span>
                {getSignalBadge(liveSignal.signal)}
              </div>
              <p className="text-xs text-slate-300 mt-1">{liveSignal.reason}</p>
            </div>
          </div>
          <div className="flex items-center space-x-3 text-xs text-slate-400 shrink-0">
            <span>Volume Confirmed: <strong className="text-slate-200">{(liveSignal.indicators?.volume || 0) >= (liveSignal.indicators?.volume_ma || 0) ? "YES" : "NO"}</strong></span>
            <span>•</span>
            <span>Rule: <strong className="text-slate-200">EMA(9) &gt; EMA(21) + RSI &gt; 50</strong></span>
          </div>
        </div>
      )}

      {/* Main Price & EMA Chart */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 sm:p-5 backdrop-blur">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 mb-4">
          <div className="flex items-center space-x-2">
            <TrendingUp className="h-5 w-5 text-emerald-400 shrink-0" />
            <h3 className="font-bold text-white text-sm sm:text-base">
              Price Action & EMAs ({selectedSymbol.replace(".NS", "")} • {timeframe})
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

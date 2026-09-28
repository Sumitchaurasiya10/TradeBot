"use client";

import React, { useEffect, useState } from "react";
import { Activity, ArrowDownRight, ArrowUpRight, BarChart2, Clock, RefreshCw } from "lucide-react";
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "../services/api";
import { IndexQuote } from "../types";

interface IndicesViewProps {
  indices: IndexQuote[];
  onRefresh?: () => void;
}

export const IndicesView: React.FC<IndicesViewProps> = ({ indices: liveIndices, onRefresh }) => {
  const [indices, setIndices] = useState<IndexQuote[]>(liveIndices);
  const [loading, setLoading] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState<string>("NIFTY 50");
  const [chartData, setChartData] = useState<any[]>([]);

  useEffect(() => {
    if (liveIndices && liveIndices.length > 0) {
      setIndices(liveIndices);
    } else {
      fetchIndices();
    }
  }, [liveIndices]);

  const fetchIndices = async () => {
    setLoading(true);
    try {
      const data = await api.getIndices(true);
      setIndices(data);
    } catch (err) {
      console.error("Failed to load indices:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Generate simulated intraday mini-chart or fetch history
    const basePrice = selectedIndex === "NIFTY 50" ? 25150 : selectedIndex === "SENSEX" ? 82400 : 53200;
    const points = [];
    let p = basePrice - 80;
    for (let i = 0; i < 25; i++) {
      p += (Math.random() - 0.48) * 20;
      points.push({
        time: `${9 + Math.floor(i / 4)}:${(i % 4) * 15 || "00"}`,
        points: Math.round(p * 100) / 100,
      });
    }
    setChartData(points);
  }, [selectedIndex]);

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-900/60 border border-slate-800 p-5 rounded-xl backdrop-blur">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">Major Benchmark Indices</h2>
          <p className="text-xs text-slate-400">
            Real-time & near-real-time index points for Indian equity markets
          </p>
        </div>
        <button
          onClick={fetchIndices}
          disabled={loading}
          className="flex items-center space-x-2 px-3.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-lg border border-slate-700 transition"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
          <span>Refresh Indices</span>
        </button>
      </div>

      {/* 3 Main Index Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {indices.map((idx) => {
          const isSelected = selectedIndex === idx.symbol;
          const isUp = (idx.change || 0) >= 0;
          return (
            <div
              key={idx.symbol}
              onClick={() => setSelectedIndex(idx.symbol)}
              className={`p-5 rounded-xl border cursor-pointer transition-all ${
                isSelected
                  ? "bg-slate-900 border-emerald-500/50 shadow-lg shadow-emerald-950/20"
                  : "bg-slate-900/60 border-slate-800 hover:border-slate-700"
              }`}
            >
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-xs font-semibold text-slate-400">{idx.exchange} INDEX</span>
                  <h3 className="text-lg font-bold text-white">{idx.symbol}</h3>
                </div>
                <span
                  className={`text-[10px] px-2 py-0.5 rounded font-mono font-semibold inline-flex items-center space-x-1 ${
                    idx.data_status === "LIVE"
                      ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                      : "bg-purple-500/10 text-purple-300 border border-purple-500/30"
                  }`}
                >
                  {idx.data_status === "LIVE" && <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse mr-1" />}
                  <span>{idx.data_status}</span>
                </span>
              </div>

              <div className="mt-4 flex items-baseline justify-between">
                <span className="text-2xl font-black font-mono text-white">
                  {Number(idx.last_price || 0).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                </span>
                <div className={`flex items-center text-xs font-bold ${isUp ? "text-emerald-400" : "text-rose-400"}`}>
                  {isUp ? <ArrowUpRight className="h-4 w-4 mr-0.5" /> : <ArrowDownRight className="h-4 w-4 mr-0.5" />}
                  <span>{isUp ? "+" : ""}{Number(idx.change || 0).toFixed(2)}</span>
                  <span className="ml-1">({isUp ? "+" : ""}{Number(idx.change_percent || 0).toFixed(2)}%)</span>
                </div>
              </div>

              {/* Day High / Low strip */}
              <div className="mt-4 pt-3 border-t border-slate-800 grid grid-cols-2 gap-2 text-[11px] text-slate-400">
                <div>
                  <span className="block text-slate-500">Day High</span>
                  <span className="font-mono text-slate-300">{idx.high ? Number(idx.high).toLocaleString("en-IN") : "—"}</span>
                </div>
                <div>
                  <span className="block text-slate-500">Day Low</span>
                  <span className="font-mono text-slate-300">{idx.low ? Number(idx.low).toLocaleString("en-IN") : "—"}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Intraday Chart for Selected Index */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <BarChart2 className="h-4 w-4 text-emerald-400" />
              <span>{selectedIndex} Intraday Price Action</span>
            </h3>
            <p className="text-xs text-slate-400">Continuous session trajectory across 15-minute intervals</p>
          </div>
        </div>

        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="indexGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="time" stroke="#475569" fontSize={11} tickLine={false} />
              <YAxis domain={["auto", "auto"]} stroke="#475569" fontSize={11} tickLine={false} orientation="right" />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#0f172a",
                  borderColor: "#334155",
                  borderRadius: "8px",
                  fontSize: "12px",
                }}
              />
              <Area type="monotone" dataKey="points" stroke="#10b981" strokeWidth={2} fillOpacity={1} fill="url(#indexGrad)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};
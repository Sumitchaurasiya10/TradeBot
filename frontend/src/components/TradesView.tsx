"use client";

import React, { useState, useEffect } from "react";
import { Trade, Stock } from "../types";
import { api } from "../services/api";

interface TradesViewProps {
  stocks: Stock[];
}

export const TradesView: React.FC<TradesViewProps> = ({ stocks }) => {
  const [trades, setTrades] = useState<Trade[]>([]);
  const [loading, setLoading] = useState(false);
  const [symbolFilter, setSymbolFilter] = useState("ALL");
  const [sideFilter, setSideFilter] = useState<"ALL" | "BUY" | "SELL">("ALL");

  const fetchTrades = async () => {
    setLoading(true);
    try {
      const data = await api.getTrades();
      setTrades(data);
    } catch (err) {
      console.error("Failed to load trades:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTrades();
  }, []);

  const filteredTrades = trades.filter((t) => {
    if (symbolFilter !== "ALL" && t.symbol !== symbolFilter) return false;
    if (sideFilter !== "ALL" && t.side !== sideFilter) return false;
    return true;
  });

  const totalRealizedPnl = filteredTrades.reduce(
    (acc, t) => acc + (t.realized_pnl || 0),
    0
  );
  const totalFees = filteredTrades.reduce((acc, t) => acc + (t.fees || 0), 0);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-900 border border-slate-800 p-4 rounded-xl">
        <div>
          <h2 className="text-xl font-bold text-slate-100">Trade Audit Log</h2>
          <p className="text-xs text-slate-400">
            Immutable log of all executed simulated trades with slippage & regulatory cost breakdown
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <select
            value={symbolFilter}
            onChange={(e) => setSymbolFilter(e.target.value)}
            className="bg-slate-800 border border-slate-700 text-slate-200 text-sm rounded-lg px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-emerald-500"
          >
            <option value="ALL">All Symbols</option>
            {stocks.map((s) => (
              <option key={s.id} value={s.symbol}>
                {s.symbol}
              </option>
            ))}
          </select>

          <div className="flex rounded-lg bg-slate-800 p-0.5 border border-slate-700 text-xs font-semibold">
            {(["ALL", "BUY", "SELL"] as const).map((side) => (
              <button
                key={side}
                onClick={() => setSideFilter(side)}
                className={`px-3 py-1 rounded-md transition-colors ${
                  sideFilter === side
                    ? "bg-emerald-500 text-slate-950 shadow-sm"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                {side}
              </button>
            ))}
          </div>

          <button
            onClick={fetchTrades}
            disabled={loading}
            className="px-3 py-1.5 text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-lg transition-colors flex items-center gap-1.5"
          >
            <svg
              className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
            Refresh
          </button>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
          <div className="text-xs text-slate-400">Total Filtered Trades</div>
          <div className="text-xl font-bold text-slate-200 mt-1">
            {filteredTrades.length}
          </div>
        </div>
        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
          <div className="text-xs text-slate-400">Total Fees / Costs Paid</div>
          <div className="text-xl font-bold text-amber-400 mt-1">
            ₹{totalFees.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
        </div>
        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
          <div className="text-xs text-slate-400">Net Realized P&L</div>
          <div
            className={`text-xl font-bold mt-1 ${
              totalRealizedPnl >= 0 ? "text-emerald-400" : "text-rose-400"
            }`}
          >
            {totalRealizedPnl >= 0 ? "+" : ""}₹
            {totalRealizedPnl.toLocaleString("en-IN", {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            })}
          </div>
        </div>
        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
          <div className="text-xs text-slate-400">Execution Mode</div>
          <div className="text-xl font-bold text-emerald-400 mt-1">
            Paper (Simulated)
          </div>
        </div>
      </div>

      {/* Trades Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-lg">
        {loading && trades.length === 0 ? (
          <div className="p-12 text-center text-slate-400">Loading trade log...</div>
        ) : filteredTrades.length === 0 ? (
          <div className="p-12 text-center text-slate-500">
            <svg
              className="w-12 h-12 mx-auto mb-3 text-slate-600 opacity-60"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            No simulated trades recorded yet. Place orders via the Paper Trading tab!
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-800/60 text-xs font-semibold text-slate-400 uppercase tracking-wider border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4">Trade ID</th>
                  <th className="py-3 px-4">Timestamp (IST)</th>
                  <th className="py-3 px-4">Symbol</th>
                  <th className="py-3 px-4">Side</th>
                  <th className="py-3 px-4 text-right">Quantity</th>
                  <th className="py-3 px-4 text-right">Price (₹)</th>
                  <th className="py-3 px-4 text-right">Total Value (₹)</th>
                  <th className="py-3 px-4 text-right">Taxes & Costs (₹)</th>
                  <th className="py-3 px-4 text-right">Realized P&L (₹)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono text-xs">
                {filteredTrades.map((t) => {
                  const val = t.quantity * t.price;
                  const isBuy = t.side === "BUY";
                  return (
                    <tr
                      key={t.trade_id}
                      className="hover:bg-slate-800/30 transition-colors"
                    >
                      <td className="py-3 px-4 text-slate-400">#{t.trade_id}</td>
                      <td className="py-3 px-4 text-slate-300">
                        {new Date(t.timestamp).toLocaleString("en-IN", {
                          timeZone: "Asia/Kolkata",
                        })}
                      </td>
                      <td className="py-3 px-4 font-bold text-slate-100">
                        {t.symbol}
                      </td>
                      <td className="py-3 px-4 font-sans">
                        <span
                          className={`inline-flex px-2 py-0.5 rounded text-[11px] font-bold ${
                            isBuy
                              ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                              : "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                          }`}
                        >
                          {t.side}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right text-slate-200">
                        {t.quantity}
                      </td>
                      <td className="py-3 px-4 text-right text-slate-200">
                        ₹{t.price.toFixed(2)}
                      </td>
                      <td className="py-3 px-4 text-right text-slate-200">
                        ₹
                        {val.toLocaleString("en-IN", {
                          minimumFractionDigits: 2,
                          maximumFractionDigits: 2,
                        })}
                      </td>
                      <td className="py-3 px-4 text-right text-amber-400/90">
                        ₹{t.fees.toFixed(2)}
                      </td>
                      <td
                        className={`py-3 px-4 text-right font-semibold ${
                          t.realized_pnl == null
                            ? "text-slate-500"
                            : t.realized_pnl >= 0
                            ? "text-emerald-400"
                            : "text-rose-400"
                        }`}
                      >
                        {t.realized_pnl != null
                          ? `${t.realized_pnl >= 0 ? "+" : ""}₹${t.realized_pnl.toFixed(2)}`
                          : "—"}
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
  );
};

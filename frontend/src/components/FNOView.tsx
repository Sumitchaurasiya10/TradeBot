"use client";

import React, { useEffect, useState } from "react";
import { Activity, ArrowDownRight, ArrowUpRight, Filter, Layers, RefreshCw, ShieldAlert } from "lucide-react";
import { api } from "../services/api";
import { OptionChainResponse, OptionChainStrikeRow } from "../types";

export const FNOView: React.FC = () => {
  const [underlying, setUnderlying] = useState<string>("NIFTY");
  const [expiry, setExpiry] = useState<string>("");
  const [availableExpiries, setAvailableExpiries] = useState<string[]>([]);
  const [chain, setChain] = useState<OptionChainResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const underlyingsList = [
    { label: "NIFTY 50 (Index)", value: "NIFTY" },
    { label: "BANK NIFTY (Index)", value: "BANK NIFTY" },
    { label: "RELIANCE (Stock)", value: "RELIANCE" },
    { label: "TCS (Stock)", value: "TCS" },
    { label: "INFY (Stock)", value: "INFY" },
    { label: "HDFCBANK (Stock)", value: "HDFCBANK" },
  ];

  const loadOptionChain = async (selectedUnd: string, selectedExp?: string) => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.getOptionChain(selectedUnd, selectedExp, true);
      setChain(res);
      setAvailableExpiries(res.available_expiries);
      if (!selectedExp && res.expiry) {
        setExpiry(res.expiry);
      }
    } catch (err: any) {
      console.error("Failed to load option chain:", err);
      setError(err.message || "Failed to fetch F&O Option Chain");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadOptionChain(underlying);
  }, [underlying]);

  const handleExpiryChange = (newExp: string) => {
    setExpiry(newExp);
    loadOptionChain(underlying, newExp);
  };

  const spot = chain?.underlying_price || 0;
  const strikes = chain?.strikes || [];

  return (
    <div className="space-y-6">
      {/* Header and Controls */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-xl font-bold text-white tracking-tight">F&O Option Chain</h2>
              <span className={`text-[10px] px-2 py-0.5 rounded font-mono font-bold inline-flex items-center space-x-1 ${
                chain?.data_status === "LIVE"
                  ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                  : "bg-purple-500/10 text-purple-300 border border-purple-500/30"
              }`}>
                {chain?.data_status === "LIVE" && <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse mr-1" />}
                <span>{chain?.data_status || "LIVE"}</span>
              </span>
            </div>
            <p className="text-xs text-slate-400">
              NSE Derivatives chain: Calls, Strike Prices, Puts, Open Interest & Implied Volatility
            </p>
          </div>

          {/* Filters */}
          <div className="flex flex-wrap items-center gap-3">
            {/* Underlying Selector */}
            <div>
              <label className="block text-[10px] uppercase font-semibold text-slate-400 mb-1">Underlying</label>
              <select
                value={underlying}
                onChange={(e) => setUnderlying(e.target.value)}
                className="bg-slate-800 border border-slate-700 text-slate-100 text-xs rounded-lg px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-emerald-500"
              >
                {underlyingsList.map((u) => (
                  <option key={u.value} value={u.value}>
                    {u.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Expiry Selector */}
            <div>
              <label className="block text-[10px] uppercase font-semibold text-slate-400 mb-1">Contract Expiry</label>
              <select
                value={expiry}
                onChange={(e) => handleExpiryChange(e.target.value)}
                className="bg-slate-800 border border-slate-700 text-slate-100 text-xs rounded-lg px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-emerald-500 font-mono"
              >
                {availableExpiries.map((exp) => (
                  <option key={exp} value={exp}>
                    {exp}
                  </option>
                ))}
              </select>
            </div>

            {/* Refresh */}
            <div className="self-end">
              <button
                onClick={() => loadOptionChain(underlying, expiry)}
                disabled={loading}
                className="flex items-center space-x-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-lg border border-slate-700 transition"
              >
                <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
                <span>Refresh</span>
              </button>
            </div>
          </div>
        </div>

        {/* Spot Price Info Strip */}
        <div className="mt-4 pt-4 border-t border-slate-800 flex flex-wrap items-center justify-between gap-4 text-xs">
          <div className="flex items-center space-x-2">
            <span className="text-slate-400">Underlying Spot LTP:</span>
            <span className="text-base font-bold font-mono text-emerald-400">
              ₹{spot.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
            </span>
          </div>
          <div className="flex items-center space-x-4 text-slate-400">
            <span>Selected Expiry: <strong className="text-slate-200 font-mono">{expiry || "—"}</strong></span>
            <span>Total Strikes: <strong className="text-slate-200 font-mono">{strikes.length}</strong></span>
          </div>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs">
          {error}
        </div>
      )}

      {/* Option Chain Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-center text-xs">
            <thead>
              {/* Header row 1: CALLS vs STRIKE vs PUTS */}
              <tr className="bg-slate-800 text-xs font-bold uppercase tracking-wider border-b border-slate-700">
                <th colSpan={6} className="py-2.5 px-3 bg-emerald-950/40 text-emerald-400 border-r border-slate-700">
                  CALL OPTIONS (CE)
                </th>
                <th className="py-2.5 px-4 bg-slate-800 text-white">STRIKE</th>
                <th colSpan={6} className="py-2.5 px-3 bg-rose-950/40 text-rose-400 border-l border-slate-700">
                  PUT OPTIONS (PE)
                </th>
              </tr>
              {/* Header row 2: Detailed metric columns */}
              <tr className="bg-slate-800/80 text-[11px] font-semibold text-slate-400 border-b border-slate-700 font-sans">
                {/* Calls */}
                <th className="py-2 px-2 text-right">OI</th>
                <th className="py-2 px-2 text-right">Chg OI</th>
                <th className="py-2 px-2 text-right">Volume</th>
                <th className="py-2 px-2 text-right">IV%</th>
                <th className="py-2 px-2 text-right">LTP (₹)</th>
                <th className="py-2 px-2 text-right border-r border-slate-700">Chg</th>

                {/* Strike */}
                <th className="py-2 px-4 bg-slate-800 text-amber-300 font-bold">Strike</th>

                {/* Puts */}
                <th className="py-2 px-2 text-left border-l border-slate-700">Chg</th>
                <th className="py-2 px-2 text-left">LTP (₹)</th>
                <th className="py-2 px-2 text-left">IV%</th>
                <th className="py-2 px-2 text-left">Volume</th>
                <th className="py-2 px-2 text-left">Chg OI</th>
                <th className="py-2 px-2 text-left">OI</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono text-[11px]">
              {strikes.map((row) => {
                const isATM = Math.abs(Number(row.strike_price) - spot) <= (spot > 5000 ? 50 : 20);
                const call = row.call;
                const put = row.put;

                const callUp = (call?.change || 0) >= 0;
                const putUp = (put?.change || 0) >= 0;

                return (
                  <tr
                    key={row.strike_price}
                    className={`transition-colors ${
                      isATM ? "bg-amber-500/10 font-bold" : "hover:bg-slate-800/40"
                    }`}
                  >
                    {/* Call Columns */}
                    <td className="py-2 px-2 text-right text-slate-300">
                      {call?.open_interest ? call.open_interest.toLocaleString("en-IN") : "—"}
                    </td>
                    <td className={`py-2 px-2 text-right ${(call?.change_in_oi || 0) >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                      {call?.change_in_oi ? `${call.change_in_oi >= 0 ? "+" : ""}${call.change_in_oi.toLocaleString("en-IN")}` : "—"}
                    </td>
                    <td className="py-2 px-2 text-right text-slate-400">
                      {call?.volume ? call.volume.toLocaleString("en-IN") : "—"}
                    </td>
                    <td className="py-2 px-2 text-right text-slate-400">
                      {call?.implied_volatility ? `${call.implied_volatility}%` : "—"}
                    </td>
                    <td className="py-2 px-2 text-right font-bold text-white">
                      {call?.last_price != null ? `₹${Number(call.last_price).toFixed(2)}` : "—"}
                    </td>
                    <td className={`py-2 px-2 text-right border-r border-slate-700 font-semibold ${callUp ? "text-emerald-400" : "text-rose-400"}`}>
                      {call?.change != null ? `${callUp ? "+" : ""}${Number(call.change).toFixed(2)}` : "—"}
                    </td>

                    {/* Strike Price Column */}
                    <td className={`py-2 px-4 font-bold ${isATM ? "bg-amber-500/20 text-amber-300 font-extrabold" : "bg-slate-800/50 text-slate-200"}`}>
                      {Number(row.strike_price || 0).toLocaleString("en-IN")}
                      {isATM && <span className="ml-1 text-[9px] px-1 py-0.2 rounded bg-amber-400/20 text-amber-300">ATM</span>}
                    </td>

                    {/* Put Columns */}
                    <td className={`py-2 px-2 text-left border-l border-slate-700 font-semibold ${putUp ? "text-emerald-400" : "text-rose-400"}`}>
                      {put?.change != null ? `${putUp ? "+" : ""}${Number(put.change).toFixed(2)}` : "—"}
                    </td>
                    <td className="py-2 px-2 text-left font-bold text-white">
                      {put?.last_price != null ? `₹${Number(put.last_price).toFixed(2)}` : "—"}
                    </td>
                    <td className="py-2 px-2 text-left text-slate-400">
                      {put?.implied_volatility ? `${put.implied_volatility}%` : "—"}
                    </td>
                    <td className="py-2 px-2 text-left text-slate-400">
                      {put?.volume ? put.volume.toLocaleString("en-IN") : "—"}
                    </td>
                    <td className={`py-2 px-2 text-left ${(put?.change_in_oi || 0) >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                      {put?.change_in_oi ? `${put.change_in_oi >= 0 ? "+" : ""}${put.change_in_oi.toLocaleString("en-IN")}` : "—"}
                    </td>
                    <td className="py-2 px-2 text-left text-slate-300">
                      {put?.open_interest ? put.open_interest.toLocaleString("en-IN") : "—"}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
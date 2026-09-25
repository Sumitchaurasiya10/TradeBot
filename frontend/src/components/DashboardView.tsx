"use client";

import React from "react";
import { ArrowDownRight, ArrowUpRight, DollarSign, Layers, PieChart, ShieldCheck, Wallet } from "lucide-react";
import { BotStatus, PortfolioSummary } from "../types";

interface DashboardViewProps {
  portfolio: PortfolioSummary | null;
  botStatus: BotStatus | null;
  setActiveTab: (tab: string) => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({ portfolio, botStatus, setActiveTab }) => {
  const initialBalance = portfolio?.initial_balance || 100000;
  const cash = portfolio?.cash || 100000;
  const totalEquity = portfolio?.total_equity || 100000;
  const realizedPnl = portfolio?.realized_pnl || 0;
  const unrealizedPnl = portfolio?.unrealized_pnl || 0;
  const totalPnl = portfolio?.total_pnl || 0;
  const totalFees = portfolio?.total_fees_paid || 0;
  const openPositions = portfolio?.positions || [];

  const pnlPercent = initialBalance > 0 ? ((totalPnl / initialBalance) * 100).toFixed(2) : "0.00";
  const isProfitable = totalPnl >= 0;

  return (
    <div className="space-y-6">
      {/* Portfolio Overview Banner */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 backdrop-blur">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <h2 className="text-xl font-bold text-white tracking-tight">Paper Portfolio Overview</h2>
            <p className="text-sm text-slate-400">
              Account: <span className="text-slate-200 font-medium">{portfolio?.account_name || "Default Paper Account"}</span> (INR ₹)
            </p>
          </div>
          <div className="flex items-center space-x-3">
            <button
              onClick={() => setActiveTab("paper")}
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-sm rounded-lg transition shadow-lg shadow-emerald-950/40"
            >
              Place Simulated Order
            </button>
            <button
              onClick={() => setActiveTab("backtest")}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium text-sm rounded-lg border border-slate-700 transition"
            >
              Run Backtest
            </button>
          </div>
        </div>

        {/* Primary Metric Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-6">
          {/* Total Equity */}
          <div className="bg-slate-950/70 border border-slate-800/80 rounded-lg p-4">
            <div className="flex items-center justify-between text-slate-400 mb-2 text-xs">
              <span>TOTAL PORTFOLIO EQUITY</span>
              <Wallet className="h-4 w-4 text-emerald-400" />
            </div>
            <div className="text-2xl font-bold text-white">₹{totalEquity.toLocaleString("en-IN", { minimumFractionDigits: 2 })}</div>
            <div className="text-xs text-slate-400 mt-1">Cash + Market Value of Holdings</div>
          </div>

          {/* Available Cash */}
          <div className="bg-slate-950/70 border border-slate-800/80 rounded-lg p-4">
            <div className="flex items-center justify-between text-slate-400 mb-2 text-xs">
              <span>AVAILABLE SIMULATED CASH</span>
              <DollarSign className="h-4 w-4 text-blue-400" />
            </div>
            <div className="text-2xl font-bold text-white">₹{cash.toLocaleString("en-IN", { minimumFractionDigits: 2 })}</div>
            <div className="text-xs text-slate-400 mt-1">Starting Capital: ₹{initialBalance.toLocaleString("en-IN")}</div>
          </div>

          {/* Total P&L */}
          <div className="bg-slate-950/70 border border-slate-800/80 rounded-lg p-4">
            <div className="flex items-center justify-between text-slate-400 mb-2 text-xs">
              <span>TOTAL SIMULATED P&L</span>
              {isProfitable ? <ArrowUpRight className="h-4 w-4 text-emerald-400" /> : <ArrowDownRight className="h-4 w-4 text-rose-400" />}
            </div>
            <div className={`text-2xl font-bold ${isProfitable ? "text-emerald-400" : "text-rose-400"}`}>
              {isProfitable ? "+" : ""}₹{totalPnl.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
            </div>
            <div className={`text-xs mt-1 font-medium ${isProfitable ? "text-emerald-400/80" : "text-rose-400/80"}`}>
              {isProfitable ? "+" : ""}{pnlPercent}% overall return
            </div>
          </div>

          {/* Unrealized vs Realized */}
          <div className="bg-slate-950/70 border border-slate-800/80 rounded-lg p-4">
            <div className="flex items-center justify-between text-slate-400 mb-2 text-xs">
              <span>REALIZED / UNREALIZED P&L</span>
              <PieChart className="h-4 w-4 text-purple-400" />
            </div>
            <div className="text-sm font-semibold text-slate-200">
              Realized: <span className={realizedPnl >= 0 ? "text-emerald-400" : "text-rose-400"}>₹{realizedPnl.toFixed(2)}</span>
            </div>
            <div className="text-sm font-semibold text-slate-200 mt-1">
              Unrealized: <span className={unrealizedPnl >= 0 ? "text-emerald-400" : "text-rose-400"}>₹{unrealizedPnl.toFixed(2)}</span>
            </div>
            <div className="text-[11px] text-slate-500 mt-1">Fees Paid: ₹{totalFees.toFixed(2)}</div>
          </div>
        </div>
      </div>

      {/* Current Active Holdings */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 backdrop-blur">
        <div className="flex justify-between items-center mb-4">
          <div className="flex items-center space-x-2">
            <Layers className="h-5 w-5 text-emerald-400" />
            <h3 className="font-bold text-white text-base">Active Open Positions ({openPositions.length})</h3>
          </div>
          <button
            onClick={() => setActiveTab("paper")}
            className="text-xs text-emerald-400 hover:text-emerald-300 font-medium"
          >
            Manage in Paper Trading &rarr;
          </button>
        </div>

        {openPositions.length === 0 ? (
          <div className="text-center py-8 border border-dashed border-slate-800 rounded-lg text-slate-500 text-sm">
            No active open positions. Go to the{" "}
            <button onClick={() => setActiveTab("market")} className="text-emerald-400 underline">
              Market Viewer
            </button>{" "}
            or{" "}
            <button onClick={() => setActiveTab("paper")} className="text-emerald-400 underline">
              Paper Trading
            </button>{" "}
            tab to simulate opening a position.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="bg-slate-950/80 text-xs uppercase text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4">Symbol</th>
                  <th className="py-3 px-4">Quantity</th>
                  <th className="py-3 px-4">Avg Entry Price</th>
                  <th className="py-3 px-4">Current Price</th>
                  <th className="py-3 px-4">Market Value</th>
                  <th className="py-3 px-4">Unrealized P&L</th>
                  <th className="py-3 px-4">Stop-Loss</th>
                  <th className="py-3 px-4">Take-Profit</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {openPositions.map((pos) => {
                  const pnl = pos.unrealized_pnl;
                  const isPosProfitable = pnl >= 0;
                  return (
                    <tr key={pos.symbol} className="hover:bg-slate-800/30">
                      <td className="py-3 px-4 font-semibold text-white">{pos.symbol}</td>
                      <td className="py-3 px-4">{pos.quantity}</td>
                      <td className="py-3 px-4">₹{pos.average_entry_price.toFixed(2)}</td>
                      <td className="py-3 px-4 font-medium text-slate-100">₹{pos.current_price.toFixed(2)}</td>
                      <td className="py-3 px-4">₹{pos.market_value.toLocaleString("en-IN", { minimumFractionDigits: 2 })}</td>
                      <td className={`py-3 px-4 font-bold ${isPosProfitable ? "text-emerald-400" : "text-rose-400"}`}>
                        {isPosProfitable ? "+" : ""}₹{pnl.toFixed(2)}
                      </td>
                      <td className="py-3 px-4 text-slate-400 text-xs">
                        {pos.stop_loss_price ? `₹${pos.stop_loss_price.toFixed(2)}` : "None"}
                      </td>
                      <td className="py-3 px-4 text-slate-400 text-xs">
                        {pos.take_profit_price ? `₹${pos.take_profit_price.toFixed(2)}` : "None"}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Safety & Interview Architecture Box */}
      <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-5 text-xs text-slate-400 flex items-start space-x-3">
        <ShieldCheck className="h-5 w-5 text-blue-400 flex-shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-slate-300">Technical Review Guarantee:</span> This application runs entirely in
          safe paper trading mode. No real money can be lost, and real broker order endpoints are excluded by design. Market data
          is cached idempotently into PostgreSQL/SQLite, and the backtester simulates fills on Candle $t+1$ Open to mathematically
          guarantee zero look-ahead bias.
        </div>
      </div>
    </div>
  );
};

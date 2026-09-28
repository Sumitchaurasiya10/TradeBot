"use client";

import React from "react";
import {
  Activity,
  ArrowDownRight,
  ArrowUpRight,
  ChevronRight,
  DollarSign,
  Layers,
  PieChart,
  ShieldCheck,
  TrendingUp,
  Wallet,
} from "lucide-react";
import { BotStatus, IndexQuote, PortfolioSummary, Quote } from "../types";

interface DashboardViewProps {
  portfolio: PortfolioSummary | null;
  botStatus: BotStatus | null;
  indices?: IndexQuote[];
  quotes?: Record<string, Quote>;
  setActiveTab: (tab: string) => void;
  onSelectStock?: (symbol: string) => void;
  onOpenTradeModal?: (symbol: string, side?: "BUY" | "SELL") => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({
  portfolio,
  botStatus,
  indices = [],
  quotes = {},
  setActiveTab,
  onSelectStock,
  onOpenTradeModal,
}) => {
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

  const coreWatchlist = [
    { symbol: "RELIANCE", name: "Reliance Industries", sector: "Energy & Retail" },
    { symbol: "TCS", name: "Tata Consultancy Services", sector: "IT Services" },
    { symbol: "INFY", name: "Infosys Limited", sector: "IT Services" },
    { symbol: "HDFCBANK", name: "HDFC Bank Limited", sector: "Banking" },
    { symbol: "ICICIBANK", name: "ICICI Bank Limited", sector: "Banking" },
    { symbol: "SBIN", name: "State Bank of India", sector: "Banking (PSU)" },
    { symbol: "ITC", name: "ITC Limited", sector: "FMCG" },
    { symbol: "LT", name: "Larsen & Toubro", sector: "Infrastructure" },
  ];

  return (
    <div className="space-y-6">
      {/* 1. Benchmark Indices Live Strip */}
      {indices.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {indices.map((idx) => {
            const isUp = (idx.change || 0) >= 0;
            return (
              <div
                key={idx.symbol}
                onClick={() => setActiveTab("indices")}
                className="bg-slate-900/80 border border-slate-800 hover:border-slate-700 p-4 rounded-xl cursor-pointer transition shadow-md"
              >
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-slate-400">{idx.exchange} INDEX</span>
                  <span
                    className={`inline-flex items-center space-x-1 px-1.5 py-0.5 rounded text-[10px] font-mono font-bold ${
                      idx.data_status === "LIVE"
                        ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                        : "bg-purple-500/10 text-purple-300 border border-purple-500/30"
                    }`}
                  >
                    {idx.data_status === "LIVE" && <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse mr-1" />}
                    <span>{idx.data_status}</span>
                  </span>
                </div>
                <div className="mt-2 flex items-baseline justify-between">
                  <span className="text-base font-bold text-white tracking-tight">{idx.symbol}</span>
                  <span className="text-lg font-black font-mono text-white">
                    {Number(idx.last_price || 0).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                  </span>
                </div>
                <div className={`mt-1 flex items-center justify-end text-xs font-semibold ${isUp ? "text-emerald-400" : "text-rose-400"}`}>
                  {isUp ? <ArrowUpRight className="h-3.5 w-3.5 mr-0.5" /> : <ArrowDownRight className="h-3.5 w-3.5 mr-0.5" />}
                  <span>{isUp ? "+" : ""}{Number(idx.change || 0).toFixed(2)} ({isUp ? "+" : ""}{Number(idx.change_percent || 0).toFixed(2)}%)</span>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* 2. Portfolio Overview Banner */}
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
              onClick={() => setActiveTab("fno")}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium text-sm rounded-lg border border-slate-700 transition"
            >
              F&O Option Chain
            </button>
          </div>
        </div>

        {/* Portfolio Stats Grid */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mt-6">
          <div className="bg-slate-950/60 p-4 rounded-lg border border-slate-800">
            <div className="flex items-center justify-between text-slate-400 text-xs">
              <span>Total Equity</span>
              <PieChart className="h-4 w-4 text-emerald-400" />
            </div>
            <div className="mt-2 text-xl font-bold font-mono text-white">
              ₹{totalEquity.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </div>
            <div className="mt-1 text-xs text-slate-500">Includes cash & open market value</div>
          </div>

          <div className="bg-slate-950/60 p-4 rounded-lg border border-slate-800">
            <div className="flex items-center justify-between text-slate-400 text-xs">
              <span>Available Cash</span>
              <Wallet className="h-4 w-4 text-blue-400" />
            </div>
            <div className="mt-2 text-xl font-bold font-mono text-white">
              ₹{cash.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </div>
            <div className="mt-1 text-xs text-slate-500">Unallocated buying power</div>
          </div>

          <div className="bg-slate-950/60 p-4 rounded-lg border border-slate-800">
            <div className="flex items-center justify-between text-slate-400 text-xs">
              <span>Total Simulated P&L</span>
              <span className={`flex items-center ${isProfitable ? "text-emerald-400" : "text-rose-400"}`}>
                {isProfitable ? <ArrowUpRight className="h-4 w-4" /> : <ArrowDownRight className="h-4 w-4" />}
                {pnlPercent}%
              </span>
            </div>
            <div className={`mt-2 text-xl font-bold font-mono ${isProfitable ? "text-emerald-400" : "text-rose-400"}`}>
              {isProfitable ? "+" : ""}₹{totalPnl.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </div>
            <div className="mt-1 text-xs text-slate-500">
              Realized: ₹{realizedPnl.toFixed(2)} | Unrealized: ₹{unrealizedPnl.toFixed(2)}
            </div>
          </div>

          <div className="bg-slate-950/60 p-4 rounded-lg border border-slate-800">
            <div className="flex items-center justify-between text-slate-400 text-xs">
              <span>Taxes & Slippage Paid</span>
              <ShieldCheck className="h-4 w-4 text-amber-400" />
            </div>
            <div className="mt-2 text-xl font-bold font-mono text-amber-400">
              ₹{totalFees.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </div>
            <div className="mt-1 text-xs text-slate-500">STT, GST, SEBI & exchange costs</div>
          </div>
        </div>
      </div>

      {/* 3. Live Watchlist Section */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-lg">
        <div className="p-5 border-b border-slate-800 flex items-center justify-between">
          <div>
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-emerald-400" />
              <span>Indian Equities Watchlist</span>
            </h3>
            <p className="text-xs text-slate-400">Live & near-real-time quotes across core NSE large-cap equities</p>
          </div>
          <button
            onClick={() => setActiveTab("market")}
            className="text-xs text-emerald-400 hover:text-emerald-300 flex items-center gap-1 font-semibold"
          >
            <span>Open Advanced Chart</span>
            <ChevronRight className="h-3.5 w-3.5" />
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-800/60 text-xs font-semibold text-slate-400 uppercase tracking-wider border-b border-slate-800">
              <tr>
                <th className="py-3 px-4">Symbol</th>
                <th className="py-3 px-4">Company</th>
                <th className="py-3 px-4 text-right">LTP (₹)</th>
                <th className="py-3 px-4 text-right">Change</th>
                <th className="py-3 px-4 text-right">Day Range (₹)</th>
                <th className="py-3 px-4 text-right">Volume</th>
                <th className="py-3 px-4 text-center">Feed Status</th>
                <th className="py-3 px-4 text-center">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono text-xs">
              {coreWatchlist.map((stock) => {
                const quote = quotes[stock.symbol];
                const price = Number(quote?.last_price || 0);
                const change = Number(quote?.change || 0);
                const pct = Number(quote?.change_percent || 0);
                const isUp = change >= 0;
                const statusTag = quote?.data_status || "DELAYED";

                return (
                  <tr key={stock.symbol} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-3 px-4 font-bold text-white">{stock.symbol}</td>
                    <td className="py-3 px-4 font-sans text-slate-300">
                      <div>{stock.name}</div>
                      <div className="text-[10px] text-slate-500">{stock.sector}</div>
                    </td>
                    <td className="py-3 px-4 text-right font-bold text-white">
                      {price > 0 ? `₹${price.toLocaleString("en-IN", { minimumFractionDigits: 2 })}` : "—"}
                    </td>
                    <td className={`py-3 px-4 text-right font-semibold ${isUp ? "text-emerald-400" : "text-rose-400"}`}>
                      {price > 0 ? `${isUp ? "+" : ""}${change.toFixed(2)} (${isUp ? "+" : ""}${pct.toFixed(2)}%)` : "—"}
                    </td>
                    <td className="py-3 px-4 text-right text-slate-400">
                      {quote?.high && quote?.low ? `₹${Number(quote.low).toFixed(1)} - ₹${Number(quote.high).toFixed(1)}` : "—"}
                    </td>
                    <td className="py-3 px-4 text-right text-slate-400">
                      {quote?.volume ? Number(quote.volume).toLocaleString("en-IN") : "—"}
                    </td>
                    <td className="py-3 px-4 text-center font-sans">
                      <span
                        className={`inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-bold ${
                          statusTag === "LIVE"
                            ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                            : statusTag === "DEMO DATA"
                            ? "bg-purple-500/10 text-purple-400 border border-purple-500/20"
                            : "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                        }`}
                      >
                        {statusTag === "LIVE" && <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse mr-1" />}
                        <span>{statusTag}</span>
                      </span>
                    </td>
                    <td className="py-3 px-4 text-center font-sans">
                      <div className="flex items-center justify-center space-x-1.5">
                        <button
                          onClick={() => {
                            if (onSelectStock) onSelectStock(stock.symbol);
                            setActiveTab("market");
                          }}
                          className="px-2 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-[11px] transition"
                        >
                          Chart
                        </button>
                        <button
                          onClick={() => {
                            if (onOpenTradeModal) {
                              onOpenTradeModal(stock.symbol, "BUY");
                            } else {
                              setActiveTab("paper");
                            }
                          }}
                          className="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded text-[11px] transition shadow"
                          title={`Buy ${stock.symbol}`}
                        >
                          B
                        </button>
                        <button
                          onClick={() => {
                            if (onOpenTradeModal) {
                              onOpenTradeModal(stock.symbol, "SELL");
                            } else {
                              setActiveTab("paper");
                            }
                          }}
                          className="px-2.5 py-1 bg-rose-600 hover:bg-rose-500 text-white font-bold rounded text-[11px] transition shadow"
                          title={`Sell ${stock.symbol}`}
                        >
                          S
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* 4. Active Open Positions */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-lg">
        <div className="p-5 border-b border-slate-800 flex items-center justify-between">
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <Layers className="h-5 w-5 text-blue-400" />
            <span>Open Paper Positions ({openPositions.length})</span>
          </h3>
          <button
            onClick={() => setActiveTab("paper")}
            className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1 font-semibold"
          >
            <span>Manage Orders</span>
            <ChevronRight className="h-3.5 w-3.5" />
          </button>
        </div>

        {openPositions.length === 0 ? (
          <div className="p-8 text-center text-slate-500 text-sm">
            No active positions in simulated account. Place a simulated BUY order via the Paper Trading tab!
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-800/60 text-xs font-semibold text-slate-400 uppercase tracking-wider border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4">Symbol</th>
                  <th className="py-3 px-4 text-right">Quantity</th>
                  <th className="py-3 px-4 text-right">Avg Entry (₹)</th>
                  <th className="py-3 px-4 text-right">Current Price (₹)</th>
                  <th className="py-3 px-4 text-right">Market Value (₹)</th>
                  <th className="py-3 px-4 text-right">Unrealized P&L (₹)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono text-xs">
                {openPositions.map((pos) => {
                  const isProfitable = pos.unrealized_pnl >= 0;
                  return (
                    <tr key={pos.symbol} className="hover:bg-slate-800/30">
                      <td className="py-3 px-4 font-bold text-white">{pos.symbol}</td>
                      <td className="py-3 px-4 text-right text-slate-200">{pos.quantity}</td>
                      <td className="py-3 px-4 text-right text-slate-300">₹{pos.average_entry_price.toFixed(2)}</td>
                      <td className="py-3 px-4 text-right text-slate-200">₹{pos.current_price.toFixed(2)}</td>
                      <td className="py-3 px-4 text-right text-slate-200">₹{pos.market_value.toLocaleString("en-IN")}</td>
                      <td className={`py-3 px-4 text-right font-bold ${isProfitable ? "text-emerald-400" : "text-rose-400"}`}>
                        {isProfitable ? "+" : ""}₹{pos.unrealized_pnl.toFixed(2)}
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
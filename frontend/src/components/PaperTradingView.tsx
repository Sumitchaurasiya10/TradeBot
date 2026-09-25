"use client";

import React, { useState } from "react";
import { AlertCircle, CheckCircle2, DollarSign, Layers, PlusCircle, RefreshCw, Send, ShieldCheck, TrendingDown, TrendingUp } from "lucide-react";
import { api } from "../services/api";
import { OrderResponse, PortfolioSummary, Position, Stock } from "../types";

interface PaperTradingViewProps {
  stocks: Stock[];
  portfolio: PortfolioSummary | null;
  onRefreshPortfolio: () => void;
}

export const PaperTradingView: React.FC<PaperTradingViewProps> = ({
  stocks,
  portfolio,
  onRefreshPortfolio,
}) => {
  const [symbol, setSymbol] = useState("TCS.NS");
  const [side, setSide] = useState<"BUY" | "SELL">("BUY");
  const [quantity, setQuantity] = useState(5);
  const [price, setPrice] = useState(3500.0);
  const [stopLossPct, setStopLossPct] = useState<number | undefined>(0.02);
  const [takeProfitPct, setTakeProfitPct] = useState<number | undefined>(0.05);

  const [loading, setLoading] = useState(false);
  const [lastOrder, setLastOrder] = useState<OrderResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const cash = portfolio?.cash || 0;
  const positions = portfolio?.positions || [];
  const currentPos = positions.find((p) => p.symbol === symbol);

  // Estimates
  const orderValue = quantity * price;
  const estimatedFees = orderValue * 0.0015; // ~0.15% approximate fee representation

  const handlePlaceOrder = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError(null);
      setLastOrder(null);

      const res = await api.placeOrder({
        symbol,
        side,
        quantity,
        price,
        stop_loss_pct: stopLossPct,
        take_profit_pct: takeProfitPct,
      });

      setLastOrder(res);
      if (res.status === "FILLED") {
        onRefreshPortfolio();
      }
    } catch (err: any) {
      setError(err.message || "Failed to submit paper order");
    } finally {
      setLoading(false);
    }
  };

  const handleQuickClose = (pos: Position) => {
    setSymbol(pos.symbol);
    setSide("SELL");
    setQuantity(pos.quantity);
    setPrice(pos.current_price);
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Order Entry Form */}
      <div className="lg:col-span-1 bg-slate-900/60 border border-slate-800 rounded-xl p-6 backdrop-blur space-y-5">
        <div className="flex items-center space-x-2 border-b border-slate-800/80 pb-3">
          <Send className="h-5 w-5 text-emerald-400" />
          <h2 className="text-base font-bold text-white tracking-tight">Simulate Order Execution</h2>
        </div>

        <form onSubmit={handlePlaceOrder} className="space-y-4">
          {/* Side Toggle */}
          <div className="grid grid-cols-2 gap-2 p-1 bg-slate-950 rounded-lg border border-slate-800">
            <button
              type="button"
              onClick={() => setSide("BUY")}
              className={`py-2 text-xs font-bold rounded-md transition ${
                side === "BUY"
                  ? "bg-emerald-600 text-white shadow-md shadow-emerald-950/50"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              BUY (Long)
            </button>
            <button
              type="button"
              onClick={() => setSide("SELL")}
              className={`py-2 text-xs font-bold rounded-md transition ${
                side === "SELL"
                  ? "bg-rose-600 text-white shadow-md shadow-rose-950/50"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              SELL (Close)
            </button>
          </div>

          {/* Symbol */}
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
            {currentPos && (
              <span className="text-[11px] text-emerald-400 mt-1 block">
                Currently holding: {currentPos.quantity} shares (Avg: ₹{currentPos.average_entry_price.toFixed(2)})
              </span>
            )}
          </div>

          {/* Quantity & Price */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">Quantity</label>
              <input
                type="number"
                value={quantity}
                onChange={(e) => setQuantity(Math.max(1, Number(e.target.value)))}
                min={1}
                className="w-full bg-slate-950 border border-slate-700 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-emerald-500"
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">Execution Price (₹)</label>
              <input
                type="number"
                step="0.5"
                value={price}
                onChange={(e) => setPrice(Math.max(0.01, Number(e.target.value)))}
                min={0.01}
                className="w-full bg-slate-950 border border-slate-700 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-emerald-500"
              />
            </div>
          </div>

          {/* Brackets (Optional on Buy) */}
          {side === "BUY" && (
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">Stop-Loss %</label>
                <input
                  type="number"
                  step="0.01"
                  value={stopLossPct}
                  onChange={(e) => setStopLossPct(Number(e.target.value))}
                  className="w-full bg-slate-950 border border-slate-700 text-white rounded-lg px-3 py-1.5 text-xs focus:outline-none"
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">Take-Profit %</label>
                <input
                  type="number"
                  step="0.01"
                  value={takeProfitPct}
                  onChange={(e) => setTakeProfitPct(Number(e.target.value))}
                  className="w-full bg-slate-950 border border-slate-700 text-white rounded-lg px-3 py-1.5 text-xs focus:outline-none"
                />
              </div>
            </div>
          )}

          {/* Live Order Estimate Preview */}
          <div className="p-3 bg-slate-950/80 border border-slate-800 rounded-lg text-xs space-y-1.5 text-slate-400">
            <div className="flex justify-between">
              <span>Gross Order Value:</span>
              <span className="font-semibold text-white">₹{orderValue.toLocaleString("en-IN", { minimumFractionDigits: 2 })}</span>
            </div>
            <div className="flex justify-between">
              <span>Estimated Statutory Fees:</span>
              <span className="text-slate-300">₹{estimatedFees.toFixed(2)}</span>
            </div>
            <div className="flex justify-between border-t border-slate-800 pt-1.5 font-bold">
              <span>Available Cash:</span>
              <span className="text-emerald-400">₹{cash.toLocaleString("en-IN", { minimumFractionDigits: 2 })}</span>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className={`w-full py-3 rounded-lg text-white font-bold text-sm transition shadow-lg ${
              side === "BUY"
                ? "bg-emerald-600 hover:bg-emerald-500 shadow-emerald-950/40"
                : "bg-rose-600 hover:bg-rose-500 shadow-rose-950/40"
            } disabled:opacity-50`}
          >
            {loading ? "Simulating Order..." : `Submit Paper ${side} Order`}
          </button>
        </form>

        {/* Order Feedback Alert */}
        {lastOrder && (
          <div
            className={`p-4 rounded-lg text-xs ${
              lastOrder.status === "FILLED"
                ? "bg-emerald-500/10 border border-emerald-500/30 text-emerald-300"
                : "bg-rose-500/10 border border-rose-500/30 text-rose-300"
            }`}
          >
            <div className="flex items-center space-x-1.5 font-bold mb-1">
              {lastOrder.status === "FILLED" ? (
                <>
                  <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                  <span>Order Filled Successfully!</span>
                </>
              ) : (
                <>
                  <AlertCircle className="h-4 w-4 text-rose-400" />
                  <span>Order Rejected</span>
                </>
              )}
            </div>
            {lastOrder.status === "FILLED" ? (
              <div>
                Executed {lastOrder.quantity} shares of {lastOrder.symbol} at ₹{lastOrder.executed_price?.toFixed(2)} (Fees: ₹{lastOrder.fees.toFixed(2)})
              </div>
            ) : (
              <div>Reason: {lastOrder.rejection_reason}</div>
            )}
          </div>
        )}

        {error && (
          <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded-lg text-rose-400 text-xs">
            {error}
          </div>
        )}
      </div>

      {/* Open Positions & Holdings */}
      <div className="lg:col-span-2 bg-slate-900/60 border border-slate-800 rounded-xl p-6 backdrop-blur space-y-4">
        <div className="flex justify-between items-center border-b border-slate-800/80 pb-3">
          <div className="flex items-center space-x-2">
            <Layers className="h-5 w-5 text-emerald-400" />
            <h2 className="text-base font-bold text-white tracking-tight">
              Active Holdings ({positions.length})
            </h2>
          </div>
          <button
            onClick={onRefreshPortfolio}
            className="flex items-center space-x-1 text-xs text-slate-400 hover:text-emerald-400 transition"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            <span>Refresh</span>
          </button>
        </div>

        {positions.length === 0 ? (
          <div className="text-center py-12 text-slate-500 text-sm border border-dashed border-slate-800 rounded-lg">
            No open paper positions. Submit a BUY order on the left panel to test execution.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="bg-slate-950/80 text-xs uppercase text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="py-3 px-3">Symbol</th>
                  <th className="py-3 px-3">Qty</th>
                  <th className="py-3 px-3">Avg Price</th>
                  <th className="py-3 px-3">Current</th>
                  <th className="py-3 px-3">Market Value</th>
                  <th className="py-3 px-3">Unrealized P&L</th>
                  <th className="py-3 px-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {positions.map((pos) => {
                  const isProfitable = pos.unrealized_pnl >= 0;
                  return (
                    <tr key={pos.symbol} className="hover:bg-slate-800/30">
                      <td className="py-3 px-3 font-bold text-white">{pos.symbol}</td>
                      <td className="py-3 px-3">{pos.quantity}</td>
                      <td className="py-3 px-3">₹{pos.average_entry_price.toFixed(2)}</td>
                      <td className="py-3 px-3 font-semibold text-slate-100">₹{pos.current_price.toFixed(2)}</td>
                      <td className="py-3 px-3 font-medium">₹{pos.market_value.toLocaleString("en-IN", { minimumFractionDigits: 2 })}</td>
                      <td className={`py-3 px-3 font-bold ${isProfitable ? "text-emerald-400" : "text-rose-400"}`}>
                        {isProfitable ? "+" : ""}₹{pos.unrealized_pnl.toFixed(2)}
                      </td>
                      <td className="py-3 px-3 text-right">
                        <button
                          onClick={() => handleQuickClose(pos)}
                          className="px-2.5 py-1 text-xs font-semibold rounded bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 transition"
                        >
                          Close
                        </button>
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

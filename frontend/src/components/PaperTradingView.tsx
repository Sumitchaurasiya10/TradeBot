"use client";

import React, { useEffect, useState } from "react";
import {
  AlertCircle,
  ArrowDownRight,
  ArrowUpRight,
  CheckCircle2,
  DollarSign,
  Info,
  Layers,
  Loader2,
  PlusCircle,
  RefreshCw,
  Send,
  ShieldCheck,
  TrendingDown,
  TrendingUp,
} from "lucide-react";
import { api } from "../services/api";
import { OrderResponse, PortfolioSummary, Position, Quote, Stock } from "../types";

interface PaperTradingViewProps {
  stocks: Stock[];
  portfolio: PortfolioSummary | null;
  onRefreshPortfolio: () => void;
  onOpenTradeModal?: (symbol: string, side?: "BUY" | "SELL") => void;
}

export const PaperTradingView: React.FC<PaperTradingViewProps> = ({
  stocks,
  portfolio,
  onRefreshPortfolio,
  onOpenTradeModal,
}) => {
  const [symbol, setSymbol] = useState("TCS.NS");
  const [side, setSide] = useState<"BUY" | "SELL">("BUY");
  const [orderType, setOrderType] = useState<"MARKET" | "LIMIT">("MARKET");
  const [quantity, setQuantity] = useState(5);
  const [limitPrice, setLimitPrice] = useState(0);
  const [liveQuote, setLiveQuote] = useState<Quote | null>(null);
  const [fetchingQuote, setFetchingQuote] = useState(false);
  const [stopLossPct, setStopLossPct] = useState<number | undefined>(0.02);
  const [takeProfitPct, setTakeProfitPct] = useState<number | undefined>(0.05);

  const [loading, setLoading] = useState(false);
  const [lastOrder, setLastOrder] = useState<OrderResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const cleanSymbol = symbol.replace(".NS", "").replace(".BO", "").toUpperCase();
  const fullSymbol = symbol.includes(".NS") ? symbol : `${cleanSymbol}.NS`;

  const cash = Number(portfolio?.cash || 0);
  const totalEquity = Number(portfolio?.total_equity || 100000);
  const positions = portfolio?.positions || [];
  const currentPos = positions.find(
    (p) => p.symbol === symbol || p.symbol.replace(".NS", "") === cleanSymbol
  );

  // Fetch real-time live LTP for the selected stock
  const fetchQuote = async (targetSym: string) => {
    try {
      setFetchingQuote(true);
      const clean = targetSym.replace(".NS", "").replace(".BO", "").toUpperCase();
      const q = await api.getQuote(clean, true);
      setLiveQuote(q);
      const p = Number(q.last_price || 0);
      if (orderType === "MARKET" || limitPrice === 0) {
        setLimitPrice(p);
      }
    } catch (err) {
      console.warn("Could not fetch real-time quote:", err);
    } finally {
      setFetchingQuote(false);
    }
  };

  useEffect(() => {
    if (symbol) {
      fetchQuote(symbol);
    }
  }, [symbol]);

  const ltp = Number(liveQuote?.last_price || 0);
  const change = Number(liveQuote?.change || 0);
  const changePct = Number(liveQuote?.change_percent || 0);
  const isUp = change >= 0;

  const execPrice = orderType === "MARKET" ? ltp : limitPrice;
  const orderValue = quantity * execPrice;
  const estimatedFees = orderValue * 0.0015; // ~0.15% approximate fee representation

  // 20% max allocation rule check
  const maxAllowedCapital = totalEquity * 0.2;
  const maxAllowedShares = ltp > 0 ? Math.max(1, Math.floor(maxAllowedCapital / ltp)) : 1;
  const exceedsAllocation = side === "BUY" && orderValue > maxAllowedCapital;
  const exceedsCash = side === "BUY" && orderValue > cash;

  const handlePlaceOrder = async (e: React.FormEvent) => {
    e.preventDefault();
    if (quantity <= 0) {
      setError("Quantity must be at least 1");
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setLastOrder(null);

      const res = await api.placeOrder({
        symbol: fullSymbol,
        side,
        quantity,
        price: orderType === "MARKET" ? 0.0 : limitPrice,
        order_type: orderType,
        stop_loss_pct: stopLossPct,
        take_profit_pct: takeProfitPct,
      });

      setLastOrder(res);
      if (res.status === "FILLED") {
        onRefreshPortfolio();
        fetchQuote(symbol);
      }
    } catch (err: any) {
      setError(err.message || "Failed to submit paper order");
    } finally {
      setLoading(false);
    }
  };

  const handleQuickClose = (pos: Position) => {
    if (onOpenTradeModal) {
      onOpenTradeModal(pos.symbol, "SELL");
      return;
    }
    setSymbol(pos.symbol);
    setSide("SELL");
    setQuantity(pos.quantity);
    setOrderType("MARKET");
    setLimitPrice(0);
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Order Entry Form */}
      <div className="lg:col-span-1 bg-slate-900/60 border border-slate-800 rounded-xl p-6 backdrop-blur space-y-5">
        <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
          <div className="flex items-center space-x-2">
            <Send className="h-5 w-5 text-emerald-400" />
            <h2 className="text-base font-bold text-white tracking-tight">Order Ticket</h2>
          </div>
          <span className="text-[10px] px-2 py-0.5 rounded font-mono font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 flex items-center">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse mr-1" />
            LIVE MARKET
          </span>
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
              SELL (Square Off)
            </button>
          </div>

          {/* Symbol & Live Price Pill */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-xs font-semibold text-slate-300">Target Stock</label>
              <button
                type="button"
                onClick={() => fetchQuote(symbol)}
                className="text-[10px] text-emerald-400 hover:underline flex items-center space-x-1"
              >
                <RefreshCw className={`h-2.5 w-2.5 ${fetchingQuote ? "animate-spin" : ""}`} />
                <span>Refresh LTP</span>
              </button>
            </div>
            <select
              value={symbol}
              onChange={(e) => setSymbol(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-emerald-500"
            >
              {stocks.map((s) => (
                <option key={s.symbol} value={s.symbol}>
                  {s.symbol.replace(".NS", "")} - {s.company_name}
                </option>
              ))}
            </select>

            {/* Live LTP Strip */}
            <div className="mt-2 p-2 rounded-lg bg-slate-950/60 border border-slate-800 flex items-center justify-between text-xs font-mono">
              <span className="text-slate-400">Current Market LTP:</span>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-white text-sm">
                  ₹{ltp > 0 ? ltp.toLocaleString("en-IN", { minimumFractionDigits: 2 }) : "—"}
                </span>
                {ltp > 0 && (
                  <span className={`text-[11px] font-semibold ${isUp ? "text-emerald-400" : "text-rose-400"}`}>
                    {isUp ? "+" : ""}{change.toFixed(2)} ({isUp ? "+" : ""}{changePct.toFixed(2)}%)
                  </span>
                )}
              </div>
            </div>

            {currentPos && (
              <span className="text-[11px] text-emerald-400 mt-1 block">
                Currently holding: {currentPos.quantity} shares (Avg: ₹{currentPos.average_entry_price.toFixed(2)})
              </span>
            )}
          </div>

          {/* Order Type Toggle: Market vs Limit */}
          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1">Order Execution Mode</label>
            <div className="grid grid-cols-2 gap-1 p-0.5 bg-slate-950 rounded-lg border border-slate-800 text-xs font-semibold">
              <button
                type="button"
                onClick={() => setOrderType("MARKET")}
                className={`py-1.5 rounded transition ${
                  orderType === "MARKET" ? "bg-slate-800 text-white shadow" : "text-slate-400"
                }`}
              >
                Market (LTP)
              </button>
              <button
                type="button"
                onClick={() => setOrderType("LIMIT")}
                className={`py-1.5 rounded transition ${
                  orderType === "LIMIT" ? "bg-slate-800 text-white shadow" : "text-slate-400"
                }`}
              >
                Limit
              </button>
            </div>
          </div>

          {/* Quantity & Price */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">Quantity</label>
              <div className="flex items-center bg-slate-950 border border-slate-700 rounded-lg overflow-hidden">
                <button
                  type="button"
                  onClick={() => setQuantity(Math.max(1, quantity - 1))}
                  className="px-3 py-2 text-slate-400 hover:text-white hover:bg-slate-800 transition"
                >
                  -
                </button>
                <input
                  type="number"
                  value={quantity}
                  onChange={(e) => setQuantity(Math.max(1, Number(e.target.value)))}
                  min={1}
                  className="w-full bg-transparent text-center text-white font-mono font-bold text-sm focus:outline-none"
                />
                <button
                  type="button"
                  onClick={() => setQuantity(quantity + 1)}
                  className="px-3 py-2 text-slate-400 hover:text-white hover:bg-slate-800 transition"
                >
                  +
                </button>
              </div>
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">
                Execution Price (₹) {orderType === "MARKET" && <span className="text-[10px] text-slate-400">(At LTP)</span>}
              </label>
              <input
                type="number"
                step="0.05"
                disabled={orderType === "MARKET"}
                value={orderType === "MARKET" ? (ltp > 0 ? ltp.toFixed(2) : "Fetching...") : limitPrice}
                onChange={(e) => setLimitPrice(Math.max(0.01, Number(e.target.value)))}
                min={0.01}
                className={`w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm font-mono font-bold focus:outline-none focus:border-emerald-500 ${
                  orderType === "MARKET" ? "text-slate-400 cursor-not-allowed" : "text-white"
                }`}
              />
            </div>
          </div>

          {/* Quick Quantity Chips */}
          <div className="flex items-center space-x-1.5 text-[11px]">
            <span className="text-slate-400 text-[10px] uppercase font-semibold">Quick Qty:</span>
            {[1, 5, 10, 25].map((q) => (
              <button
                key={q}
                type="button"
                onClick={() => setQuantity(q)}
                className={`px-2 py-0.5 rounded border ${
                  quantity === q
                    ? "bg-slate-800 border-slate-600 text-white font-bold"
                    : "border-slate-800 text-slate-400 hover:bg-slate-800/60"
                }`}
              >
                +{q}
              </button>
            ))}
            {side === "BUY" && maxAllowedShares > 0 && (
              <button
                type="button"
                onClick={() => setQuantity(maxAllowedShares)}
                className="px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/20 font-bold"
              >
                Max 20% ({maxAllowedShares})
              </button>
            )}
          </div>

          {/* Allocation Warning */}
          {exceedsAllocation && (
            <div className="p-3 bg-amber-500/10 border border-amber-500/30 rounded-xl text-amber-300 text-xs flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Info className="h-4 w-4 text-amber-400 shrink-0" />
                <span>Exceeds max 20% allocation rule (₹{maxAllowedCapital.toLocaleString("en-IN")})</span>
              </div>
              <button
                type="button"
                onClick={() => setQuantity(maxAllowedShares)}
                className="underline text-[11px] font-bold text-amber-200 ml-2"
              >
                Use {maxAllowedShares}
              </button>
            </div>
          )}

          {/* Live Order Estimate Preview */}
          <div className="p-3 bg-slate-950/80 border border-slate-800 rounded-lg text-xs space-y-1.5 text-slate-400 font-mono">
            <div className="flex justify-between">
              <span className="font-sans">Gross Order Value:</span>
              <span className="font-semibold text-white">₹{orderValue.toLocaleString("en-IN", { minimumFractionDigits: 2 })}</span>
            </div>
            <div className="flex justify-between">
              <span className="font-sans">Estimated Statutory Fees:</span>
              <span className="text-slate-300">₹{estimatedFees.toFixed(2)}</span>
            </div>
            <div className="flex justify-between border-t border-slate-800 pt-1.5 font-bold">
              <span className="font-sans">Available Cash:</span>
              <span className="text-emerald-400">₹{cash.toLocaleString("en-IN", { minimumFractionDigits: 2 })}</span>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading || (side === "BUY" && exceedsCash) || exceedsAllocation}
            className={`w-full py-3 rounded-lg text-white font-bold text-sm transition shadow-lg ${
              side === "BUY"
                ? "bg-emerald-600 hover:bg-emerald-500 shadow-emerald-950/40"
                : "bg-rose-600 hover:bg-rose-500 shadow-rose-950/40"
            } disabled:opacity-50`}
          >
            {loading ? "Routing Paper Order..." : `${side} ${cleanSymbol} • ${quantity} shares @ ${orderType === "MARKET" ? "Market LTP" : `₹${limitPrice.toFixed(2)}`}`}
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
                Executed {lastOrder.quantity} shares of {lastOrder.symbol} at ₹{Number(lastOrder.executed_price || ltp).toFixed(2)} (Fees: ₹{Number(lastOrder.fees).toFixed(2)})
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
            <table className="w-full text-left text-sm text-slate-300 min-w-[660px]">
              <thead className="bg-slate-950/80 text-xs uppercase text-slate-400 border-b border-slate-800 font-sans whitespace-nowrap">
                <tr>
                  <th className="py-3 px-3">Symbol</th>
                  <th className="py-3 px-3">Qty</th>
                  <th className="py-3 px-3">Avg Price</th>
                  <th className="py-3 px-3">Current LTP</th>
                  <th className="py-3 px-3">Market Value</th>
                  <th className="py-3 px-3">Unrealized P&L</th>
                  <th className="py-3 px-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono text-xs whitespace-nowrap">
                {positions.map((pos) => {
                  const isProfitable = Number(pos.unrealized_pnl) >= 0;
                  return (
                    <tr key={pos.symbol} className="hover:bg-slate-800/30">
                      <td className="py-3 px-3 font-bold text-white">{pos.symbol}</td>
                      <td className="py-3 px-3 font-bold">{pos.quantity}</td>
                      <td className="py-3 px-3">₹{Number(pos.average_entry_price).toFixed(2)}</td>
                      <td className="py-3 px-3 font-semibold text-slate-100">₹{Number(pos.current_price).toFixed(2)}</td>
                      <td className="py-3 px-3 font-medium">₹{Number(pos.market_value).toLocaleString("en-IN", { minimumFractionDigits: 2 })}</td>
                      <td className={`py-3 px-3 font-bold ${isProfitable ? "text-emerald-400" : "text-rose-400"}`}>
                        {isProfitable ? "+" : ""}₹{Number(pos.unrealized_pnl).toFixed(2)}
                      </td>
                      <td className="py-3 px-3 text-right font-sans">
                        <button
                          onClick={() => handleQuickClose(pos)}
                          className="px-2.5 py-1 text-xs font-bold rounded bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 transition shadow"
                        >
                          Square Off (Exit)
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

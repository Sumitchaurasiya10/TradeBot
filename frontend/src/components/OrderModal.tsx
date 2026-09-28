"use client";

import React, { useEffect, useState } from "react";
import {
  AlertCircle,
  ArrowDownRight,
  ArrowUpRight,
  CheckCircle2,
  DollarSign,
  Info,
  Loader2,
  RefreshCw,
  ShieldCheck,
  TrendingDown,
  TrendingUp,
  X,
} from "lucide-react";
import { api } from "../services/api";
import { OrderResponse, PortfolioSummary, Quote, Stock } from "../types";

interface OrderModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialSymbol?: string;
  initialSide?: "BUY" | "SELL";
  stocks: Stock[];
  portfolio: PortfolioSummary | null;
  quotes?: Record<string, Quote>;
  onOrderSuccess: () => void;
}

export const OrderModal: React.FC<OrderModalProps> = ({
  isOpen,
  onClose,
  initialSymbol = "TCS.NS",
  initialSide = "BUY",
  stocks,
  portfolio,
  quotes = {},
  onOrderSuccess,
}) => {
  const [symbol, setSymbol] = useState<string>(initialSymbol);
  const [side, setSide] = useState<"BUY" | "SELL">(initialSide);
  const [orderType, setOrderType] = useState<"MARKET" | "LIMIT">("MARKET");
  const [productType, setProductType] = useState<"CNC" | "MIS">("CNC");
  const [quantity, setQuantity] = useState<number>(5);
  const [limitPrice, setLimitPrice] = useState<number>(0);
  const [liveQuote, setLiveQuote] = useState<Quote | null>(null);
  const [fetchingQuote, setFetchingQuote] = useState<boolean>(false);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [successOrder, setSuccessOrder] = useState<OrderResponse | null>(null);

  // Normalize symbol cleanly
  const cleanSymbol = symbol.replace(".NS", "").replace(".BO", "").toUpperCase();
  const fullSymbol = symbol.includes(".NS") ? symbol : `${cleanSymbol}.NS`;

  // Fetch live quote for the selected stock
  const fetchLiveQuote = async (targetSym: string) => {
    try {
      setFetchingQuote(true);
      const clean = targetSym.replace(".NS", "").replace(".BO", "").toUpperCase();
      const q = await api.getQuote(clean, true);
      setLiveQuote(q);
      if (orderType === "MARKET" || limitPrice === 0) {
        setLimitPrice(Number(q.last_price || 0));
      }
    } catch (err) {
      console.warn("Could not fetch real-time quote for modal:", err);
      // Fallback to cache quote
      const cached = quotes[cleanSymbol];
      if (cached) {
        setLiveQuote(cached);
        if (orderType === "MARKET" || limitPrice === 0) {
          setLimitPrice(Number(cached.last_price || 0));
        }
      }
    } finally {
      setFetchingQuote(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      setSymbol(initialSymbol);
      setSide(initialSide);
      setError(null);
      setSuccessOrder(null);
      fetchLiveQuote(initialSymbol);
    }
  }, [isOpen, initialSymbol, initialSide]);

  useEffect(() => {
    if (isOpen && symbol) {
      fetchLiveQuote(symbol);
    }
  }, [symbol]);

  if (!isOpen) return null;

  const ltp = Number(liveQuote?.last_price || quotes[cleanSymbol]?.last_price || 0);
  const change = Number(liveQuote?.change || quotes[cleanSymbol]?.change || 0);
  const changePct = Number(liveQuote?.change_percent || quotes[cleanSymbol]?.change_percent || 0);
  const isUp = change >= 0;

  const execPrice = orderType === "MARKET" ? ltp : limitPrice;
  const orderValue = quantity * execPrice;
  const availableCash = Number(portfolio?.cash || 0);
  const totalEquity = Number(portfolio?.total_equity || 100000);

  // 20% max allocation rule check
  const maxAllowedCapital = totalEquity * 0.2;
  const maxAllowedShares = ltp > 0 ? Math.max(1, Math.floor(maxAllowedCapital / ltp)) : 1;
  const exceedsAllocation = side === "BUY" && orderValue > maxAllowedCapital;
  const exceedsCash = side === "BUY" && orderValue > availableCash;

  // Approximate statutory charges (Brokerage 0.03% + STT 0.1% + GST 18% + Exchange fees)
  const estimatedFees = orderValue * 0.0015;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (quantity <= 0) {
      setError("Quantity must be at least 1");
      return;
    }

    try {
      setSubmitting(true);
      setError(null);

      const res = await api.placeOrder({
        symbol: fullSymbol,
        side,
        quantity,
        price: orderType === "MARKET" ? 0.0 : limitPrice,
        order_type: orderType,
      });

      setSuccessOrder(res);
      onOrderSuccess();
    } catch (err: any) {
      setError(err.message || "Failed to execute paper order");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-150">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg shadow-2xl overflow-hidden flex flex-col">
        {/* Header Bar */}
        <div className={`p-4 flex items-center justify-between border-b ${
          side === "BUY" ? "bg-emerald-950/30 border-emerald-500/20" : "bg-rose-950/30 border-rose-500/20"
        }`}>
          <div className="flex items-center space-x-3">
            <div className={`px-2 py-1 rounded text-xs font-black tracking-wider uppercase ${
              side === "BUY" ? "bg-emerald-500 text-slate-950" : "bg-rose-500 text-white"
            }`}>
              {side}
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h3 className="text-base font-bold text-white tracking-tight">{cleanSymbol}</h3>
                <span className="text-[10px] px-1.5 py-0.2 rounded bg-slate-800 text-slate-300 font-mono">NSE</span>
                <span className="text-[10px] px-1.5 py-0.2 rounded bg-emerald-500/10 text-emerald-400 font-mono font-bold flex items-center">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse mr-1" />
                  LIVE
                </span>
              </div>
              <div className="flex items-center space-x-2 text-xs mt-0.5">
                <span className="text-slate-400 font-medium">LTP:</span>
                <span className="font-mono font-bold text-white">
                  ₹{ltp > 0 ? ltp.toLocaleString("en-IN", { minimumFractionDigits: 2 }) : "—"}
                </span>
                {ltp > 0 && (
                  <span className={`flex items-center text-[11px] font-semibold ${isUp ? "text-emerald-400" : "text-rose-400"}`}>
                    {isUp ? <ArrowUpRight className="h-3 w-3 mr-0.5" /> : <ArrowDownRight className="h-3 w-3 mr-0.5" />}
                    {isUp ? "+" : ""}{change.toFixed(2)} ({isUp ? "+" : ""}{changePct.toFixed(2)}%)
                  </span>
                )}
                {fetchingQuote && <Loader2 className="h-3 w-3 text-slate-400 animate-spin ml-1" />}
              </div>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Success Confirmation View */}
        {successOrder ? (
          <div className="p-6 text-center space-y-4">
            <div className="mx-auto w-12 h-12 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center">
              <CheckCircle2 className="h-7 w-7" />
            </div>
            <div>
              <h4 className="text-lg font-bold text-white">Order Executed Successfully!</h4>
              <p className="text-xs text-slate-400 mt-1">
                Order #{successOrder.order_id} &bull; {side} {quantity} shares of {cleanSymbol}
              </p>
            </div>
            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 text-xs space-y-2">
              <div className="flex justify-between">
                <span className="text-slate-400">Execution Price</span>
                <span className="font-mono font-bold text-white">₹{Number(successOrder.executed_price || ltp).toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Total Value</span>
                <span className="font-mono font-bold text-white">₹{((successOrder.executed_price || ltp) * quantity).toLocaleString("en-IN", { minimumFractionDigits: 2 })}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Estimated Statutory Fees</span>
                <span className="font-mono text-slate-300">₹{Number(successOrder.fees).toFixed(2)}</span>
              </div>
            </div>
            <div className="pt-2">
              <button
                onClick={onClose}
                className="w-full py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl font-bold text-sm transition shadow-lg shadow-emerald-950/40"
              >
                Done
              </button>
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="p-5 space-y-4">
            {/* Side Toggle Bar */}
            <div className="grid grid-cols-2 gap-2 p-1 bg-slate-950 rounded-xl border border-slate-800">
              <button
                type="button"
                onClick={() => setSide("BUY")}
                className={`py-2 text-xs font-bold rounded-lg transition ${
                  side === "BUY"
                    ? "bg-emerald-600 text-white shadow-md shadow-emerald-950/40"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                BUY (Delivery)
              </button>
              <button
                type="button"
                onClick={() => setSide("SELL")}
                className={`py-2 text-xs font-bold rounded-lg transition ${
                  side === "SELL"
                    ? "bg-rose-600 text-white shadow-md shadow-rose-950/40"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                SELL (Square Off)
              </button>
            </div>

            {/* Target Stock Selector */}
            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="text-xs font-semibold text-slate-300">Stock Symbol</label>
                <button
                  type="button"
                  onClick={() => fetchLiveQuote(symbol)}
                  className="text-[10px] text-emerald-400 hover:underline flex items-center space-x-1"
                >
                  <RefreshCw className="h-2.5 w-2.5" />
                  <span>Refresh LTP</span>
                </button>
              </div>
              <select
                value={symbol}
                onChange={(e) => setSymbol(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 text-white rounded-lg px-3 py-2 text-sm font-semibold focus:outline-none focus:border-emerald-500 font-sans"
              >
                {stocks.map((s) => (
                  <option key={s.symbol} value={s.symbol}>
                    {s.symbol.replace(".NS", "")} - {s.company_name}
                  </option>
                ))}
              </select>
            </div>

            {/* Order Type & Product Selectors */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">Order Type</label>
                <div className="grid grid-cols-2 gap-1 p-0.5 bg-slate-950 rounded-lg border border-slate-800 text-xs">
                  <button
                    type="button"
                    onClick={() => setOrderType("MARKET")}
                    className={`py-1.5 rounded font-bold transition ${
                      orderType === "MARKET" ? "bg-slate-800 text-white shadow" : "text-slate-400"
                    }`}
                  >
                    Market
                  </button>
                  <button
                    type="button"
                    onClick={() => setOrderType("LIMIT")}
                    className={`py-1.5 rounded font-bold transition ${
                      orderType === "LIMIT" ? "bg-slate-800 text-white shadow" : "text-slate-400"
                    }`}
                  >
                    Limit
                  </button>
                </div>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">Product</label>
                <div className="grid grid-cols-2 gap-1 p-0.5 bg-slate-950 rounded-lg border border-slate-800 text-xs">
                  <button
                    type="button"
                    onClick={() => setProductType("CNC")}
                    className={`py-1.5 rounded font-bold transition ${
                      productType === "CNC" ? "bg-slate-800 text-white shadow" : "text-slate-400"
                    }`}
                  >
                    CNC (Delv)
                  </button>
                  <button
                    type="button"
                    onClick={() => setProductType("MIS")}
                    className={`py-1.5 rounded font-bold transition ${
                      productType === "MIS" ? "bg-slate-800 text-white shadow" : "text-slate-400"
                    }`}
                  >
                    MIS (Intra)
                  </button>
                </div>
              </div>
            </div>

            {/* Quantity and Price Inputs */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">Quantity (Shares)</label>
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
                    min={1}
                    value={quantity}
                    onChange={(e) => setQuantity(Math.max(1, Number(e.target.value)))}
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
                  Price (₹) {orderType === "MARKET" && <span className="text-[10px] text-slate-400">(At Market LTP)</span>}
                </label>
                <input
                  type="number"
                  step="0.05"
                  disabled={orderType === "MARKET"}
                  value={orderType === "MARKET" ? ltp.toFixed(2) : limitPrice}
                  onChange={(e) => setLimitPrice(Math.max(0.01, Number(e.target.value)))}
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

            {/* Error / Warning Alerts */}
            {error && (
              <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-300 text-xs flex items-start space-x-2">
                <AlertCircle className="h-4 w-4 text-rose-400 shrink-0 mt-0.5" />
                <span>{error}</span>
              </div>
            )}

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
                  Use {maxAllowedShares} shares
                </button>
              </div>
            )}

            {/* Real-time Order Summary Sheet */}
            <div className="bg-slate-950/80 p-3.5 rounded-xl border border-slate-800 text-xs space-y-1.5 font-mono">
              <div className="flex justify-between text-slate-300">
                <span className="font-sans text-slate-400">Total Order Value</span>
                <span className="font-bold text-white">₹{orderValue.toLocaleString("en-IN", { minimumFractionDigits: 2 })}</span>
              </div>
              <div className="flex justify-between text-slate-400 text-[11px]">
                <span className="font-sans">Estimated Charges (STT, GST)</span>
                <span>₹{estimatedFees.toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-slate-400 text-[11px] pt-1 border-t border-slate-800/80">
                <span className="font-sans">Available Cash</span>
                <span className="text-slate-200">₹{availableCash.toLocaleString("en-IN", { minimumFractionDigits: 2 })}</span>
              </div>
            </div>

            {/* Action Submit Button */}
            <button
              type="submit"
              disabled={submitting || (side === "BUY" && exceedsCash) || exceedsAllocation}
              className={`w-full py-3 rounded-xl font-bold text-sm transition flex items-center justify-center space-x-2 shadow-lg ${
                side === "BUY"
                  ? "bg-emerald-600 hover:bg-emerald-500 text-white shadow-emerald-950/40 disabled:opacity-50 disabled:hover:bg-emerald-600"
                  : "bg-rose-600 hover:bg-rose-500 text-white shadow-rose-950/40 disabled:opacity-50 disabled:hover:bg-rose-600"
              }`}
            >
              {submitting ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Routing Paper Order...</span>
                </>
              ) : (
                <span>
                  {side} {cleanSymbol} &bull; {quantity} shares @ {orderType === "MARKET" ? "Market" : `₹${limitPrice.toFixed(2)}`}
                </span>
              )}
            </button>
          </form>
        )}
      </div>
    </div>
  );
};

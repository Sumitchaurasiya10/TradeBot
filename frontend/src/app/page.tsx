"use client";

import React, { useEffect, useState } from "react";
import { Header } from "../components/Header";
import { DashboardView } from "../components/DashboardView";
import { IndicesView } from "../components/IndicesView";
import { FNOView } from "../components/FNOView";
import { MarketView } from "../components/MarketView";
import { StrategyView } from "../components/StrategyView";
import { BacktestView } from "../components/BacktestView";
import { PaperTradingView } from "../components/PaperTradingView";
import { TradesView } from "../components/TradesView";
import { api } from "../services/api";
import { useMarketWebSocket } from "../hooks/useMarketWebSocket";
import { BotStatus, PortfolioSummary, Stock } from "../types";
import { AlertTriangle, RefreshCw } from "lucide-react";

export default function Home() {
  const [activeTab, setActiveTab] = useState<string>("dashboard");
  const [botStatus, setBotStatus] = useState<BotStatus | null>(null);
  const [stocks, setStocks] = useState<Stock[]>([]);
  const [portfolio, setPortfolio] = useState<PortfolioSummary | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Core 8 symbols for real-time WebSocket subscriptions
  const defaultWatchlist = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "SBIN", "ITC", "LT"];
  const { connectionState, marketStatus, indices, quotes, lastUpdated } = useMarketWebSocket(defaultWatchlist);

  const loadInitialData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [statusData, stocksData, portfolioData] = await Promise.all([
        api.getBotStatus().catch((e) => {
          console.error("Status fetch failed:", e);
          return null;
        }),
        api.getStocks().catch((e) => {
          console.error("Stocks fetch failed:", e);
          return [];
        }),
        api.getPortfolio().catch((e) => {
          console.error("Portfolio fetch failed:", e);
          return null;
        }),
      ]);

      setBotStatus(statusData);
      setStocks(stocksData || []);
      setPortfolio(portfolioData);
    } catch (err: any) {
      console.error("Failed to load application data:", err);
      setError(err.message || "Failed to connect to TradeBot backend API.");
    } finally {
      setLoading(false);
    }
  };

  const refreshPortfolio = async () => {
    try {
      const p = await api.getPortfolio();
      setPortfolio(p);
    } catch (err) {
      console.error("Failed to refresh portfolio:", err);
    }
  };

  useEffect(() => {
    loadInitialData();
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Navigation Header with Live Stream & Market Hours Status */}
      <Header
        status={botStatus}
        marketSession={marketStatus}
        connectionState={connectionState}
        lastUpdated={lastUpdated}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
      />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Error notification banner if backend is unreachable */}
        {error && (
          <div className="mb-6 p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 flex items-center justify-between text-rose-300">
            <div className="flex items-center space-x-3">
              <AlertTriangle className="h-5 w-5 text-rose-400 shrink-0" />
              <div className="text-sm">
                <span className="font-semibold">Backend Connection Issue:</span>{" "}
                {error}. Ensure the FastAPI server is running on{" "}
                <code className="bg-slate-900 px-1 py-0.5 rounded font-mono text-xs">
                  http://127.0.0.1:8000
                </code>
              </div>
            </div>
            <button
              onClick={loadInitialData}
              className="px-3 py-1 bg-rose-500/20 hover:bg-rose-500/30 border border-rose-500/30 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition"
            >
              <RefreshCw className="h-3.5 w-3.5" />
              <span>Retry</span>
            </button>
          </div>
        )}

        {/* Dynamic Views */}
        {activeTab === "dashboard" && (
          <DashboardView
            portfolio={portfolio}
            botStatus={botStatus}
            indices={indices}
            quotes={quotes}
            setActiveTab={setActiveTab}
          />
        )}

        {activeTab === "indices" && (
          <IndicesView indices={indices} onRefresh={loadInitialData} />
        )}

        {activeTab === "fno" && <FNOView />}

        {activeTab === "market" && <MarketView stocks={stocks} />}

        {activeTab === "strategy" && <StrategyView stocks={stocks} />}

        {activeTab === "backtest" && <BacktestView stocks={stocks} />}

        {activeTab === "paper" && (
          <PaperTradingView
            stocks={stocks}
            portfolio={portfolio}
            onRefreshPortfolio={refreshPortfolio}
          />
        )}

        {activeTab === "trades" && <TradesView stocks={stocks} />}
      </main>

      {/* Footer / Educational Disclaimer Banner */}
      <footer className="border-t border-slate-900 bg-slate-950 py-6 mt-12 text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-2 text-center">
          <p className="font-medium text-slate-400">
            EDUCATIONAL & PAPER TRADING DEMONSTRATION PLATFORM ONLY
          </p>
          <p className="max-w-3xl mx-auto text-slate-500 leading-relaxed">
            This platform strictly simulates trading on Indian NSE equities with realistic regulatory cost modeling (STT, Exchange Turnover, SEBI, GST, Stamp Duty & Slippage). No live brokerage accounts are integrated, no real money is deployed, and no guarantees of market returns are implied. Built for software engineering and quantitative architecture review.
          </p>
          <p className="text-[11px] text-slate-600">
            TradeBot India &bull; FastAPI Backend &bull; WebSockets &bull; Next.js 14 App Router &bull; Tailwind CSS
          </p>
        </div>
      </footer>
    </div>
  );
}
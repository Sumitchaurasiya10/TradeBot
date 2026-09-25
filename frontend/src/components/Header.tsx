"use client";

import React from "react";
import { Activity, Clock, ShieldAlert, TrendingUp } from "lucide-react";
import { BotStatus } from "../types";

interface HeaderProps {
  status: BotStatus | null;
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

export const Header: React.FC<HeaderProps> = ({ status, activeTab, setActiveTab }) => {
  const tabs = [
    { id: "dashboard", label: "Dashboard" },
    { id: "market", label: "Market Viewer" },
    { id: "strategy", label: "Strategy Signals" },
    { id: "backtest", label: "Backtesting Lab" },
    { id: "paper", label: "Paper Trading" },
    { id: "trades", label: "Trade History" },
  ];

  return (
    <header className="border-b border-slate-800 bg-slate-950/80 backdrop-blur sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Title */}
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-emerald-500/10 border border-emerald-500/20 rounded-lg text-emerald-400">
              <TrendingUp className="h-6 w-6" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-lg text-white tracking-tight">TradeBot India</span>
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 font-medium">
                  PAPER TRADING ONLY
                </span>
              </div>
              <p className="text-xs text-slate-400">NSE Algorithmic Strategy & Simulation Lab</p>
            </div>
          </div>

          {/* Status Indicators */}
          <div className="hidden md:flex items-center space-x-3 text-xs">
            {/* Market Hours */}
            <div className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-slate-900 border border-slate-800 text-slate-300">
              <Clock className="h-3.5 w-3.5 text-blue-400" />
              <span>NSE IST:</span>
              <span className={status?.is_market_open ? "text-emerald-400 font-semibold" : "text-amber-400 font-semibold"}>
                {status?.is_market_open ? "OPEN" : "CLOSED (09:15 - 15:30 IST)"}
              </span>
            </div>

            {/* Data Provider Transparency Badge */}
            <div className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-slate-900 border border-slate-800 text-slate-300">
              <Activity className="h-3.5 w-3.5 text-purple-400" />
              <span>Feed:</span>
              <span className="text-purple-300 font-medium">Yahoo Finance (Delayed ~15m)</span>
            </div>

            {/* Bot Status */}
            <div className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-emerald-950/40 border border-emerald-800 text-emerald-300">
              <div className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
              <span className="font-semibold">{status?.status || "ONLINE"}</span>
            </div>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="flex space-x-1 overflow-x-auto py-2 border-t border-slate-800/60 no-scrollbar">
          {tabs.map((tab) => {
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-all whitespace-nowrap ${
                  isActive
                    ? "bg-slate-800 text-emerald-400 border-b-2 border-emerald-500 shadow-sm"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-900/60"
                }`}
              >
                {tab.label}
              </button>
            );
          })}
        </div>
      </div>
    </header>
  );
};

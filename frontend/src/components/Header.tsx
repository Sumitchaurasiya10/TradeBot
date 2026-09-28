"use client";

import React from "react";
import { Activity, Clock, Layers, LogIn, LogOut, Radio, ShieldAlert, TrendingUp, User as UserIcon, UserPlus } from "lucide-react";
import { BotStatus, MarketSessionStatus, User } from "../types";

interface HeaderProps {
  status: BotStatus | null;
  marketSession?: MarketSessionStatus | null;
  connectionState?: "CONNECTING" | "LIVE" | "DISCONNECTED" | "ERROR";
  lastUpdated?: string;
  activeTab: string;
  setActiveTab: (tab: string) => void;
  user: User | null;
  onOpenAuth: (mode?: "login" | "register") => void;
  onLogout: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  status,
  marketSession,
  connectionState = "LIVE",
  lastUpdated,
  activeTab,
  setActiveTab,
  user,
  onOpenAuth,
  onLogout,
}) => {
  const tabs = [
    { id: "dashboard", label: "Dashboard" },
    { id: "indices", label: "Indices" },
    { id: "market", label: "Market Viewer" },
    { id: "fno", label: "F&O Lab" },
    { id: "strategy", label: "Strategy Signals" },
    { id: "paper", label: "Paper Trading" },
    { id: "trades", label: "Trade History" },
  ];

  const isSessionOpen = marketSession ? marketSession.is_open : status?.is_market_open;
  const sessionName = marketSession?.session || (isSessionOpen ? "MARKET OPEN" : "MARKET CLOSED");

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
                  100% PAPER TRADING
                </span>
              </div>
              <p className="text-xs text-slate-400">NSE Live Market Monitor & Quantitative Simulation</p>
            </div>
          </div>

          {/* Status Indicators & Auth Controls */}
          <div className="flex items-center space-x-3 text-xs">
            {/* Live Connection Badge */}
            <div className="hidden lg:flex items-center space-x-1.5 px-3 py-1 rounded-full bg-slate-900 border border-slate-800 text-slate-300">
              <span
                className={`h-2 w-2 rounded-full ${
                  connectionState === "LIVE"
                    ? "bg-emerald-400 animate-pulse"
                    : connectionState === "CONNECTING"
                    ? "bg-amber-400 animate-ping"
                    : "bg-rose-400"
                }`}
              />
              <span className="font-semibold text-slate-200">
                {connectionState === "LIVE" ? "STREAM LIVE" : connectionState}
              </span>
              {lastUpdated && <span className="text-slate-500 font-mono">({lastUpdated})</span>}
            </div>

            {/* Market Session Status */}
            <div className="hidden sm:flex items-center space-x-1.5 px-3 py-1 rounded-full bg-slate-900 border border-slate-800 text-slate-300">
              <Clock className="h-3.5 w-3.5 text-blue-400" />
              <span>NSE:</span>
              <span className={`font-semibold ${isSessionOpen ? "text-emerald-400" : "text-amber-400"}`}>
                {sessionName}
              </span>
            </div>

            {/* Zero Real Money Badge */}
            <div className="hidden md:flex items-center space-x-1 px-2.5 py-1 rounded-full bg-rose-500/10 border border-rose-500/20 text-rose-400">
              <ShieldAlert className="h-3.5 w-3.5" />
              <span>No Real Money</span>
            </div>

            {/* User Profile / Auth Actions */}
            {user ? (
              <div className="flex items-center space-x-2 pl-2 border-l border-slate-800">
                <div className="flex items-center space-x-2 bg-slate-900 border border-slate-800 px-3 py-1 rounded-full text-xs">
                  <div className="h-5 w-5 rounded-full bg-emerald-500/20 text-emerald-400 font-bold flex items-center justify-center text-[10px]">
                    {user.full_name ? user.full_name.charAt(0).toUpperCase() : user.email.charAt(0).toUpperCase()}
                  </div>
                  <div className="flex flex-col">
                    <span className="font-semibold text-slate-200 leading-tight">
                      {user.full_name || user.email.split("@")[0]}
                    </span>
                    <span className="text-[9px] text-slate-500 uppercase leading-none">{user.role}</span>
                  </div>
                </div>
                <button
                  onClick={onLogout}
                  title="Sign Out"
                  className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-slate-900 rounded-lg transition"
                >
                  <LogOut className="h-4 w-4" />
                </button>
              </div>
            ) : (
              <div className="flex items-center space-x-2 pl-2 border-l border-slate-800">
                <button
                  onClick={() => onOpenAuth("login")}
                  className="px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-300 hover:text-white hover:bg-slate-900 transition flex items-center space-x-1.5"
                >
                  <LogIn className="h-3.5 w-3.5" />
                  <span>Log In</span>
                </button>
                <button
                  onClick={() => onOpenAuth("register")}
                  className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-500 hover:bg-emerald-400 text-slate-950 transition flex items-center space-x-1.5 shadow-sm"
                >
                  <UserPlus className="h-3.5 w-3.5" />
                  <span>Register</span>
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex space-x-1 overflow-x-auto py-2 scrollbar-none border-t border-slate-900">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-colors ${
                activeTab === tab.id
                  ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-900"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>
    </header>
  );
};
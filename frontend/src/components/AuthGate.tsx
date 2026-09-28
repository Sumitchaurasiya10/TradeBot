"use client";

import React, { useState } from "react";
import {
  Activity,
  AlertCircle,
  ArrowRight,
  BarChart2,
  CheckCircle2,
  Lock,
  Mail,
  Shield,
  ShieldAlert,
  Sparkles,
  TrendingUp,
  User as UserIcon,
  Zap,
} from "lucide-react";
import { api } from "../services/api";
import { User } from "../types";

interface AuthGateProps {
  onAuthSuccess: (user: User) => void;
}

export const AuthGate: React.FC<AuthGateProps> = ({ onAuthSuccess }) => {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (mode === "login") {
        const res = await api.login({ email, password });
        onAuthSuccess(res.user);
      } else {
        const res = await api.register({
          email,
          password,
          full_name: fullName.trim() || undefined,
        });
        onAuthSuccess(res.user);
      }
    } catch (err: any) {
      setError(err.message || "Authentication failed. Please verify your credentials.");
    } finally {
      setLoading(false);
    }
  };

  const handleQuickDemoLogin = async () => {
    setError(null);
    setLoading(true);
    try {
      const res = await api.login({
        email: "demo@tradebot.in",
        password: "password123",
      });
      onAuthSuccess(res.user);
    } catch (err: any) {
      setError(err.message || "Failed to log in as demo trader.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between selection:bg-emerald-500 selection:text-slate-950">
      {/* Top Banner */}
      <header className="border-b border-slate-900 bg-slate-950/80 backdrop-blur px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-emerald-500/10 border border-emerald-500/20 rounded-xl text-emerald-400">
              <TrendingUp className="h-6 w-6" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-lg text-white tracking-tight">TradeBot India</span>
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 font-semibold tracking-wide">
                  100% PAPER TRADING
                </span>
              </div>
              <p className="text-xs text-slate-400">NSE Live Market Monitor & Quantitative Simulation</p>
            </div>
          </div>

          <div className="flex items-center space-x-3 text-xs">
            <div className="hidden sm:flex items-center space-x-1.5 px-3 py-1 rounded-full bg-slate-900 border border-slate-800 text-slate-300">
              <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
              <span className="font-semibold text-slate-200">PORTAL ONLINE</span>
            </div>
            <div className="flex items-center space-x-1 px-2.5 py-1 rounded-full bg-rose-500/10 border border-rose-500/20 text-rose-400">
              <ShieldAlert className="h-3.5 w-3.5" />
              <span>No Real Money</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 flex items-center justify-center p-6 md:p-12">
        <div className="max-w-5xl w-full grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
          {/* Left Column: Platform Features Overview */}
          <div className="lg:col-span-7 space-y-6">
            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-semibold">
              <Sparkles className="h-3.5 w-3.5" />
              <span>Authentication Gate</span>
            </div>

            <div className="space-y-3">
              <h1 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight leading-tight">
                Sign in to access your{" "}
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-teal-300">
                  Paper Trading Terminal
                </span>
              </h1>
              <p className="text-slate-400 text-sm leading-relaxed max-w-xl">
                Please log in or create an account to enter TradeBot India. Your session allows you to monitor live NSE equity streams, execute market & limit orders with ₹1,00,000 virtual balance, and track performance in real time.
              </p>
            </div>

            {/* Feature Highlights Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
              <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1.5">
                <div className="flex items-center space-x-2 text-emerald-400 font-semibold text-sm">
                  <Activity className="h-4 w-4" />
                  <span>Live NSE Streaming</span>
                </div>
                <p className="text-xs text-slate-400 leading-normal">
                  Real-time tick feeds, candlesticks, and market depth for top Indian blue-chip stocks.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1.5">
                <div className="flex items-center space-x-2 text-blue-400 font-semibold text-sm">
                  <TrendingUp className="h-4 w-4" />
                  <span>Brokerage-Grade Orders</span>
                </div>
                <p className="text-xs text-slate-400 leading-normal">
                  Instant market & limit order execution with locked live market LTP and margin guards.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1.5">
                <div className="flex items-center space-x-2 text-purple-400 font-semibold text-sm">
                  <BarChart2 className="h-4 w-4" />
                  <span>Live Option Chain & F&O</span>
                </div>
                <p className="text-xs text-slate-400 leading-normal">
                  Analyze strikes, open interest, and implied volatility across NIFTY and BANKNIFTY contracts.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1.5">
                <div className="flex items-center space-x-2 text-amber-400 font-semibold text-sm">
                  <Shield className="h-4 w-4" />
                  <span>Realistic Cost Modeling</span>
                </div>
                <p className="text-xs text-slate-400 leading-normal">
                  Accurate STT, exchange turnover fees, SEBI charges, GST, and stamp duty calculation.
                </p>
              </div>
            </div>
          </div>

          {/* Right Column: Auth Card */}
          <div className="lg:col-span-5">
            <div className="bg-slate-900/95 border border-slate-800 rounded-2xl p-6 sm:p-8 shadow-2xl shadow-slate-950 backdrop-blur">
              {/* Tab Selector */}
              <div className="flex p-1 bg-slate-950/70 border border-slate-800 rounded-xl mb-6">
                <button
                  type="button"
                  onClick={() => {
                    setMode("login");
                    setError(null);
                  }}
                  className={`flex-1 py-2 text-xs font-semibold rounded-lg transition ${
                    mode === "login"
                      ? "bg-slate-800 text-white shadow-sm"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  Log In
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setMode("register");
                    setError(null);
                  }}
                  className={`flex-1 py-2 text-xs font-semibold rounded-lg transition ${
                    mode === "register"
                      ? "bg-slate-800 text-white shadow-sm"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  Create Account
                </button>
              </div>

              {/* Title & Subtitle */}
              <div className="mb-5">
                <h2 className="text-xl font-bold text-white tracking-tight">
                  {mode === "login" ? "Welcome back" : "Create your account"}
                </h2>
                <p className="text-xs text-slate-400 mt-1">
                  {mode === "login"
                    ? "Enter your credentials to enter the trading terminal"
                    : "Fill out the form below to get your ₹1,00,000 paper trading portfolio"}
                </p>
              </div>

              {/* Error Message */}
              {error && (
                <div className="mb-4 p-3 bg-rose-500/10 border border-rose-500/30 rounded-xl flex items-start space-x-2 text-rose-300 text-xs">
                  <AlertCircle className="h-4 w-4 shrink-0 mt-0.5 text-rose-400" />
                  <span>{error}</span>
                </div>
              )}

              {/* Form */}
              <form onSubmit={handleSubmit} className="space-y-4">
                {mode === "register" && (
                  <div>
                    <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                      Full Name
                    </label>
                    <div className="relative">
                      <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
                        <UserIcon className="h-4 w-4" />
                      </div>
                      <input
                        type="text"
                        required
                        placeholder="e.g. Arjun Sharma"
                        value={fullName}
                        onChange={(e) => setFullName(e.target.value)}
                        className="w-full pl-9 pr-3 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:border-emerald-500 transition"
                      />
                    </div>
                  </div>
                )}

                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                    Email Address
                  </label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
                      <Mail className="h-4 w-4" />
                    </div>
                    <input
                      type="email"
                      required
                      placeholder="name@example.com"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="w-full pl-9 pr-3 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:border-emerald-500 transition"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                    Password
                  </label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
                      <Lock className="h-4 w-4" />
                    </div>
                    <input
                      type="password"
                      required
                      placeholder="••••••••"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className="w-full pl-9 pr-3 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:border-emerald-500 transition"
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full mt-2 py-3 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-sm rounded-xl transition duration-150 flex items-center justify-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-emerald-500/20"
                >
                  {loading ? (
                    <span className="inline-block animate-spin h-4 w-4 border-2 border-slate-950 border-t-transparent rounded-full" />
                  ) : (
                    <>
                      <span>{mode === "login" ? "Enter Terminal" : "Register & Start Trading"}</span>
                      <ArrowRight className="h-4 w-4" />
                    </>
                  )}
                </button>
              </form>

              {/* 1-Click Instant Demo Login Button */}
              <div className="mt-5 pt-5 border-t border-slate-800/80">
                <button
                  type="button"
                  disabled={loading}
                  onClick={handleQuickDemoLogin}
                  className="w-full py-2.5 bg-slate-800 hover:bg-slate-700/80 border border-slate-700/80 rounded-xl text-xs font-semibold text-slate-200 hover:text-white transition flex items-center justify-center space-x-2 group"
                >
                  <Zap className="h-4 w-4 text-amber-400 group-hover:scale-110 transition-transform" />
                  <span>1-Click Demo Login (demo@tradebot.in)</span>
                </button>
                <p className="text-[11px] text-slate-500 text-center mt-2">
                  No sign-up required &bull; Instantly explore pre-seeded paper portfolio
                </p>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Footer Disclaimer */}
      <footer className="border-t border-slate-900 bg-slate-950/80 py-4 px-6 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>&copy; {new Date().getFullYear()} TradeBot India &bull; Quantitative Paper Trading Platform</span>
          <span className="text-[11px] text-slate-600">Simulated Indian Equities &bull; Zero Real Financial Risk</span>
        </div>
      </footer>
    </div>
  );
};

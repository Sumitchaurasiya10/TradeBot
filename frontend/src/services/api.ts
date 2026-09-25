import {
  BacktestRequest,
  BacktestResponse,
  BotStatus,
  IndicatorResponse,
  MarketDataResponse,
  OrderRequest,
  OrderResponse,
  PortfolioSummary,
  Position,
  SignalRequest,
  SignalResponse,
  Stock,
  Trade,
} from "../types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorDetail = "API Request failed";
    try {
      const errJson = await res.json();
      errorDetail = errJson.detail || errorDetail;
    } catch {
      errorDetail = res.statusText || errorDetail;
    }
    throw new Error(errorDetail);
  }
  return res.json();
}

export const api = {
  async getBotStatus(): Promise<BotStatus> {
    const res = await fetch(`${API_BASE_URL}/bot/status`, { cache: "no-store" });
    return handleResponse<BotStatus>(res);
  },

  async getStocks(): Promise<Stock[]> {
    const res = await fetch(`${API_BASE_URL}/stocks`, { cache: "no-store" });
    return handleResponse<Stock[]>(res);
  },

  async getMarketData(symbol: string, forceRefresh = false): Promise<MarketDataResponse> {
    const url = `${API_BASE_URL}/stocks/${encodeURIComponent(symbol)}/market-data?force_refresh=${forceRefresh}`;
    const res = await fetch(url, { cache: "no-store" });
    return handleResponse<MarketDataResponse>(res);
  },

  async getIndicators(
    symbol: string,
    fastEma = 9,
    slowEma = 21,
    rsi = 14,
    volumeMa = 20
  ): Promise<IndicatorResponse> {
    const url = `${API_BASE_URL}/stocks/${encodeURIComponent(symbol)}/indicators?fast_ema=${fastEma}&slow_ema=${slowEma}&rsi=${rsi}&volume_ma=${volumeMa}`;
    const res = await fetch(url, { cache: "no-store" });
    return handleResponse<IndicatorResponse>(res);
  },

  async evaluateSignal(request: SignalRequest): Promise<SignalResponse> {
    const res = await fetch(`${API_BASE_URL}/strategy/signal`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    });
    return handleResponse<SignalResponse>(res);
  },

  async runBacktest(request: BacktestRequest): Promise<BacktestResponse> {
    const res = await fetch(`${API_BASE_URL}/backtest`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    });
    return handleResponse<BacktestResponse>(res);
  },

  async getPortfolio(): Promise<PortfolioSummary> {
    const res = await fetch(`${API_BASE_URL}/paper/portfolio`, { cache: "no-store" });
    return handleResponse<PortfolioSummary>(res);
  },

  async getPositions(): Promise<Position[]> {
    const res = await fetch(`${API_BASE_URL}/paper/positions`, { cache: "no-store" });
    return handleResponse<Position[]>(res);
  },

  async getTrades(): Promise<Trade[]> {
    const res = await fetch(`${API_BASE_URL}/paper/trades`, { cache: "no-store" });
    return handleResponse<Trade[]>(res);
  },

  async placeOrder(request: OrderRequest): Promise<OrderResponse> {
    const res = await fetch(`${API_BASE_URL}/paper/orders`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    });
    return handleResponse<OrderResponse>(res);
  },
};

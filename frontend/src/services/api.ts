import {
  AuthResponse,
  BacktestRequest,
  BacktestResponse,
  BotStatus,
  FNOQuote,
  IndexQuote,
  IndicatorResponse,
  LoginRequest,
  MarketDataResponse,
  MarketSessionStatus,
  OptionChainResponse,
  OrderRequest,
  OrderResponse,
  PortfolioSummary,
  Position,
  Quote,
  RegisterRequest,
  SignalRequest,
  SignalResponse,
  Stock,
  Trade,
  User,
} from "../types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";

const TOKEN_KEY = "tradebot_auth_token";

export const authStorage = {
  getToken(): string | null {
    if (typeof window === "undefined") return null;
    return localStorage.getItem(TOKEN_KEY);
  },
  setToken(token: string): void {
    if (typeof window === "undefined") return;
    localStorage.setItem(TOKEN_KEY, token);
  },
  removeToken(): void {
    if (typeof window === "undefined") return;
    localStorage.removeItem(TOKEN_KEY);
  },
};

export function getAuthHeaders(): HeadersInit {
  const token = authStorage.getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

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
  // Authentication Endpoints
  async register(request: RegisterRequest): Promise<AuthResponse> {
    const res = await fetch(`${API_BASE_URL}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    });
    const data = await handleResponse<AuthResponse>(res);
    if (data.access_token) {
      authStorage.setToken(data.access_token);
    }
    return data;
  },

  async login(request: LoginRequest): Promise<AuthResponse> {
    const res = await fetch(`${API_BASE_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    });
    const data = await handleResponse<AuthResponse>(res);
    if (data.access_token) {
      authStorage.setToken(data.access_token);
    }
    return data;
  },

  async getMe(): Promise<User> {
    const res = await fetch(`${API_BASE_URL}/auth/me`, {
      cache: "no-store",
      headers: { ...getAuthHeaders() },
    });
    return handleResponse<User>(res);
  },

  logout(): void {
    authStorage.removeToken();
  },

  async getBotStatus(): Promise<BotStatus> {

    const res = await fetch(`${API_BASE_URL}/bot/status`, { cache: "no-store" });
    return handleResponse<BotStatus>(res);
  },

  async getMarketStatus(): Promise<MarketSessionStatus> {
    const res = await fetch(`${API_BASE_URL}/market/status`, { cache: "no-store" });
    return handleResponse<MarketSessionStatus>(res);
  },

  async getIndices(forceRefresh = false): Promise<IndexQuote[]> {
    const res = await fetch(`${API_BASE_URL}/market/indices?force_refresh=${forceRefresh}`, { cache: "no-store" });
    return handleResponse<IndexQuote[]>(res);
  },

  async getQuotes(symbols?: string, forceRefresh = false): Promise<Quote[]> {
    const query = symbols ? `?symbols=${encodeURIComponent(symbols)}&force_refresh=${forceRefresh}` : `?force_refresh=${forceRefresh}`;
    const res = await fetch(`${API_BASE_URL}/market/quotes${query}`, { cache: "no-store" });
    return handleResponse<Quote[]>(res);
  },

  async getQuote(symbol: string, forceRefresh = false): Promise<Quote> {
    const res = await fetch(`${API_BASE_URL}/market/quotes/${encodeURIComponent(symbol)}?force_refresh=${forceRefresh}`, { cache: "no-store" });
    return handleResponse<Quote>(res);
  },

  async getChartHistory(symbol: string, timeframe = "1M"): Promise<any> {
    const res = await fetch(`${API_BASE_URL}/market/history/${encodeURIComponent(symbol)}?timeframe=${encodeURIComponent(timeframe)}`, { cache: "no-store" });
    return handleResponse<any>(res);
  },

  async getLiveSignal(symbol: string, params?: Record<string, any>): Promise<SignalResponse> {
    const queryParams = new URLSearchParams(params as any).toString();
    const queryStr = queryParams ? `?${queryParams}` : "";
    const res = await fetch(`${API_BASE_URL}/strategy/live-signal/${encodeURIComponent(symbol)}${queryStr}`, { cache: "no-store" });
    return handleResponse<SignalResponse>(res);
  },

  async getFnoUnderlyings(): Promise<Array<{ underlying: string; type: string; spot_price: number; data_status: string }>> {
    const res = await fetch(`${API_BASE_URL}/fno/underlyings`, { cache: "no-store" });
    return handleResponse<any>(res);
  },

  async getFnoExpiries(underlying: string): Promise<string[]> {
    const res = await fetch(`${API_BASE_URL}/fno/expiries/${encodeURIComponent(underlying)}`, { cache: "no-store" });
    return handleResponse<string[]>(res);
  },

  async getOptionChain(underlying: string, expiry?: string, forceRefresh = false): Promise<OptionChainResponse> {
    const query = expiry ? `?expiry=${encodeURIComponent(expiry)}&force_refresh=${forceRefresh}` : `?force_refresh=${forceRefresh}`;
    const res = await fetch(`${API_BASE_URL}/fno/option-chain/${encodeURIComponent(underlying)}${query}`, { cache: "no-store" });
    return handleResponse<OptionChainResponse>(res);
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
export interface Stock {
  id: number;
  symbol: string;
  company_name: string;
  sector?: string;
  is_active: boolean;
}

export interface MarketDataPoint {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface MarketDataResponse {
  symbol: string;
  data_provider: string;
  data_status: "HISTORICAL" | "LATEST_AVAILABLE_DELAYED" | "SIMULATED";
  count: number;
  bars: MarketDataPoint[];
}

export interface IndicatorDataPoint {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  fast_ema?: number | null;
  slow_ema?: number | null;
  rsi?: number | null;
  volume_ma?: number | null;
}

export interface IndicatorResponse {
  symbol: string;
  fast_ema_period: number;
  slow_ema_period: number;
  rsi_period: number;
  volume_ma_period: number;
  bars: IndicatorDataPoint[];
}

export interface SignalRequest {
  symbol: string;
  fast_ema_period: number;
  slow_ema_period: number;
  rsi_period: number;
  rsi_entry_threshold: number;
  rsi_max_threshold: number;
  rsi_exit_threshold: number;
  volume_ma_period: number;
  volume_multiplier: number;
}

export interface SignalResponse {
  signal: "BUY" | "SELL" | "HOLD";
  timestamp: string;
  symbol: string;
  reason: string;
  indicators: {
    fast_ema?: number | null;
    slow_ema?: number | null;
    rsi?: number | null;
    volume?: number | null;
    volume_ma?: number | null;
    close?: number | null;
  };
  parameters: Record<string, any>;
}

export interface BacktestRequest {
  symbol: string;
  initial_capital: number;
  fast_ema_period: number;
  slow_ema_period: number;
  rsi_period: number;
  rsi_entry_threshold: number;
  rsi_max_threshold: number;
  rsi_exit_threshold: number;
  volume_ma_period: number;
  volume_multiplier: number;
  stop_loss_pct: number;
  take_profit_pct: number;
  position_size_pct: number;
}

export interface BacktestTrade {
  trade_id: number;
  symbol: string;
  entry_timestamp: string;
  exit_timestamp: string;
  entry_price: number;
  exit_price: number;
  quantity: number;
  gross_pnl: number;
  net_pnl: number;
  fees_paid: number;
  return_pct: number;
  exit_reason: string;
}

export interface EquityPoint {
  timestamp: string;
  equity: number;
  cash: number;
  drawdown_pct: number;
}

export interface BacktestResponse {
  id?: number;
  symbol: string;
  strategy_name: string;
  parameters: Record<string, any>;
  initial_capital: number;
  final_equity: number;
  total_return_pct: number;
  benchmark_return_pct: number;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate_pct: number;
  average_trade_return_pct: number;
  max_drawdown_pct: number;
  profit_factor: number;
  total_transaction_costs: number;
  equity_curve: EquityPoint[];
  trades: BacktestTrade[];
}

export interface OrderRequest {
  symbol: string;
  side: "BUY" | "SELL";
  quantity: number;
  price: number;
  stop_loss_pct?: number;
  take_profit_pct?: number;
}

export interface OrderResponse {
  order_id: number;
  symbol: string;
  side: "BUY" | "SELL";
  quantity: number;
  requested_price: number;
  executed_price?: number | null;
  status: "FILLED" | "REJECTED" | "CANCELLED";
  fees: number;
  timestamp: string;
  rejection_reason?: string | null;
}

export interface Position {
  symbol: string;
  quantity: number;
  average_entry_price: number;
  current_price: number;
  market_value: number;
  unrealized_pnl: number;
  stop_loss_price?: number | null;
  take_profit_price?: number | null;
}

export interface Trade {
  trade_id: number;
  order_id: number;
  symbol: string;
  side: "BUY" | "SELL";
  quantity: number;
  price: number;
  fees: number;
  realized_pnl?: number | null;
  timestamp: string;
}

export interface PortfolioSummary {
  account_name: string;
  currency: string;
  initial_balance: number;
  cash: number;
  total_equity: number;
  realized_pnl: number;
  unrealized_pnl: number;
  total_pnl: number;
  total_fees_paid: number;
  open_positions_count: number;
  positions: Position[];
}

export interface BotStatus {
  status: string;
  environment: string;
  paper_trading_mode: boolean;
  real_money_trading: boolean;
  data_provider: string;
  data_provider_notice: string;
  market_timezone: string;
  market_hours: string;
  is_market_open: boolean;
  supported_symbols: string[];
}

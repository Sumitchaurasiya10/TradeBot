from decimal import Decimal
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore',
    )

    ENVIRONMENT: str = 'development'
    LOG_LEVEL: str = 'INFO'
    PROJECT_NAME: str = 'Indian Stock Market Paper Trading Bot'
    API_V1_STR: str = '/api/v1'

    # Database: SQLite fallback for local dev, PostgreSQL for production
    DATABASE_URL: str = 'sqlite+aiosqlite:///./tradebot.db'

    # Indian Market Universe (NSE tickers)
    SUPPORTED_SYMBOLS: List[str] = [
        'RELIANCE.NS',
        'TCS.NS',
        'INFY.NS',
        'HDFCBANK.NS',
        'ICICIBANK.NS',
    ]

    # Market Timezone and Hours
    MARKET_TIMEZONE: str = 'Asia/Kolkata'
    MARKET_OPEN_TIME: str = '09:15'
    MARKET_CLOSE_TIME: str = '15:30'

    # Risk Management & Paper Trading Defaults
    DEFAULT_INITIAL_CAPITAL: Decimal = Decimal('100000.00')
    DEFAULT_STOP_LOSS_PCT: Decimal = Decimal('0.02')
    DEFAULT_TAKE_PROFIT_PCT: Decimal = Decimal('0.05')
    MAX_CAPITAL_PER_TRADE_PCT: Decimal = Decimal('0.20')
    MAX_OPEN_POSITIONS: int = 5

    # Market Data Provider
    MARKET_DATA_PROVIDER: str = 'yfinance'


settings = Settings()

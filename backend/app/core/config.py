from decimal import Decimal
from typing import List, Optional, Union
from pydantic import field_validator
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

    # Authentication & Security
    SECRET_KEY: str = 'quantdesk-india-super-secret-jwt-key-2026'
    ALGORITHM: str = 'HS256'
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # CORS configuration
    CORS_ORIGINS: Union[List[str], str] = [
        'http://localhost:3000',
        'http://127.0.0.1:3000',
        'http://localhost:8000',
        'http://127.0.0.1:8000',
    ]

    @field_validator('CORS_ORIGINS', mode='after')
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            import json
            if v.startswith('[') and v.endswith(']'):
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(',') if i.strip()]
        return v

    # Database: SQLite fallback for local dev, PostgreSQL for production
    DATABASE_URL: str = 'sqlite+aiosqlite:///./tradebot.db'

    # Indian Market Universe (NSE tickers)
    SUPPORTED_SYMBOLS: List[str] = [
        'RELIANCE.NS',
        'TCS.NS',
        'INFY.NS',
        'HDFCBANK.NS',
        'ICICIBANK.NS',
        'SBIN.NS',
        'ITC.NS',
        'LT.NS',
    ]

    # Major Benchmark Indices
    SUPPORTED_INDICES: List[str] = [
        'NIFTY 50',
        'SENSEX',
        'BANK NIFTY',
    ]

    # Supported F&O Underlyings
    SUPPORTED_FNO_UNDERLYINGS: List[str] = [
        'NIFTY',
        'BANK NIFTY',
        'RELIANCE',
        'TCS',
        'INFY',
        'HDFCBANK',
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

    # Market Data Provider: 'hybrid', 'mock', 'yfinance', 'angel_one', 'kite'
    LIVE_DATA_PROVIDER: str = 'hybrid'
    MARKET_DATA_PROVIDER: str = 'yfinance'

    # Optional Broker Credentials (Never commit real values)
    ANGEL_ONE_API_KEY: Optional[str] = None
    ANGEL_ONE_CLIENT_CODE: Optional[str] = None
    ANGEL_ONE_PIN: Optional[str] = None
    ANGEL_ONE_TOTP_SECRET: Optional[str] = None

    KITE_API_KEY: Optional[str] = None
    KITE_API_SECRET: Optional[str] = None
    KITE_ACCESS_TOKEN: Optional[str] = None


settings = Settings()
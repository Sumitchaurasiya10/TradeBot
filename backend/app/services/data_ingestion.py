from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, Set
import pandas as pd
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.logging import logger
from backend.app.models.stock import MarketData, Stock
from backend.app.services.data_provider import DataProvider
from backend.app.services.data_validator import DataValidator
from backend.app.services.yfinance_provider import YFinanceProvider


def _to_utc_key(dt) -> str:
    """Normalizes a datetime to an ISO string for reliable cross-engine key comparison."""
    if hasattr(dt, "to_pydatetime"):
        dt = dt.to_pydatetime()
    if getattr(dt, "tzinfo", None) is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


class DataIngestionService:
    """
    Orchestrates market data fetching, validation, and idempotent database caching.
    """

    def __init__(self, default_provider: Optional[DataProvider] = None):
        self.default_provider = default_provider or YFinanceProvider()

    async def get_or_create_stock(self, session: AsyncSession, symbol: str) -> Stock:
        clean_symbol = DataValidator.validate_symbol(symbol)
        stmt = select(Stock).where(Stock.symbol == clean_symbol)
        result = await session.execute(stmt)
        stock = result.scalars().first()

        if not stock:
            names = {
                "RELIANCE.NS": "Reliance Industries Limited",
                "TCS.NS": "Tata Consultancy Services Limited",
                "INFY.NS": "Infosys Limited",
                "HDFCBANK.NS": "HDFC Bank Limited",
                "ICICIBANK.NS": "ICICI Bank Limited",
            }
            sectors = {
                "RELIANCE.NS": "Energy & Conglomerate",
                "TCS.NS": "Information Technology",
                "INFY.NS": "Information Technology",
                "HDFCBANK.NS": "Banking & Financials",
                "ICICIBANK.NS": "Banking & Financials",
            }
            stock = Stock(
                symbol=clean_symbol,
                company_name=names.get(clean_symbol, clean_symbol),
                sector=sectors.get(clean_symbol, "Diversified"),
                is_active=True,
            )
            session.add(stock)
            await session.commit()
            await session.refresh(stock)

        return stock

    async def get_or_fetch_market_data(
        self,
        session: AsyncSession,
        symbol: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        force_refresh: bool = False,
        provider: Optional[DataProvider] = None,
    ) -> pd.DataFrame:
        """
        Retrieves market data from the local database cache if available;
        otherwise fetches from the provider, validates, and idempotently caches to DB.
        """
        stock = await self.get_or_create_stock(session, symbol)
        active_provider = provider or self.default_provider

        # 1. Check existing cached data if not forcing refresh
        if not force_refresh:
            stmt = select(MarketData).where(MarketData.stock_id == stock.id).order_by(MarketData.timestamp.asc())
            if start_date:
                stmt = stmt.where(MarketData.timestamp >= start_date)
            if end_date:
                stmt = stmt.where(MarketData.timestamp <= end_date)

            result = await session.execute(stmt)
            cached_rows = result.scalars().all()

            if cached_rows and len(cached_rows) >= 20:
                logger.info(f"Loaded {len(cached_rows)} cached market data records for '{symbol}' from database.")
                records = [
                    {
                        "timestamp": row.timestamp,
                        "open": float(row.open),
                        "high": float(row.high),
                        "low": float(row.low),
                        "close": float(row.close),
                        "volume": int(row.volume),
                    }
                    for row in cached_rows
                ]
                return pd.DataFrame(records)

        # 2. Fetch from provider
        logger.info(f"Cache miss or refresh requested for '{symbol}'. Ingesting from provider '{active_provider.get_provider_name()}'...")
        raw_df = active_provider.fetch_ohlcv(symbol=symbol, start_date=start_date, end_date=end_date)
        validated_df = DataValidator.validate_and_normalize(raw_df, symbol)

        # 3. Idempotent Caching: Compare using UTC string keys
        existing_stmt = select(MarketData.timestamp).where(MarketData.stock_id == stock.id)
        existing_res = await session.execute(existing_stmt)
        existing_keys: Set[str] = {
            _to_utc_key(t) for t in existing_res.scalars().all()
        }

        new_entities = []
        for _, row in validated_df.iterrows():
            ts_key = _to_utc_key(row["timestamp"])
            if ts_key not in existing_keys:
                ts_to_store = row["timestamp"]
                if hasattr(ts_to_store, "to_pydatetime"):
                    ts_to_store = ts_to_store.to_pydatetime()

                new_entities.append(MarketData(
                    stock_id=stock.id,
                    timestamp=ts_to_store,
                    open=Decimal(str(round(row["open"], 4))),
                    high=Decimal(str(round(row["high"], 4))),
                    low=Decimal(str(round(row["low"], 4))),
                    close=Decimal(str(round(row["close"], 4))),
                    volume=int(row["volume"]),
                    provider=active_provider.get_provider_name(),
                ))
                existing_keys.add(ts_key)

        if new_entities:
            session.add_all(new_entities)
            await session.commit()
            logger.info(f"Successfully cached {len(new_entities)} new market data rows for '{symbol}' in database.")

        return validated_df

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import random
import pytest
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from backend.app.database.session import async_session_factory
from backend.app.models import MarketData, PaperAccount, Stock
from backend.app.services.data_ingestion import DataIngestionService
from backend.app.services.data_provider import MockDataProvider


@pytest.mark.asyncio
async def test_database_seeded_stocks_exist():
    async with async_session_factory() as session:
        stocks = (await session.execute(select(Stock))).scalars().all()
        symbols = [s.symbol for s in stocks]
        assert "RELIANCE.NS" in symbols
        assert "TCS.NS" in symbols
        assert "INFY.NS" in symbols


@pytest.mark.asyncio
async def test_paper_account_seeded():
    async with async_session_factory() as session:
        account = (await session.execute(select(PaperAccount))).scalars().first()
        assert account is not None
        assert account.initial_balance == Decimal("100000.00")
        assert account.currency == "INR"


@pytest.mark.asyncio
async def test_market_data_unique_constraint_enforced():
    async with async_session_factory() as session:
        stock = (await session.execute(select(Stock).where(Stock.symbol == "TCS.NS"))).scalars().first()
        assert stock is not None
        stock_id = int(stock.id)

        # Unique timestamp for this run
        unique_offset = random.randint(10000, 999999)
        dt = datetime(2050, 1, 1, 9, 15, tzinfo=timezone.utc) + timedelta(minutes=unique_offset)

        m1 = MarketData(
            stock_id=stock_id,
            timestamp=dt,
            open=Decimal("3500.00"),
            high=Decimal("3550.00"),
            low=Decimal("3480.00"),
            close=Decimal("3520.00"),
            volume=500000,
            provider="test",
        )
        session.add(m1)
        await session.commit()

        # Attempt to insert identical (stock_id, timestamp)
        m2 = MarketData(
            stock_id=stock_id,
            timestamp=dt,
            open=Decimal("3510.00"),
            high=Decimal("3560.00"),
            low=Decimal("3490.00"),
            close=Decimal("3530.00"),
            volume=600000,
            provider="test",
        )
        session.add(m2)
        with pytest.raises(IntegrityError):
            await session.commit()
        await session.rollback()

        # Clean up using pre-fetched integer stock_id
        await session.execute(delete(MarketData).where(MarketData.stock_id == stock_id, MarketData.timestamp == dt))
        await session.commit()


@pytest.mark.asyncio
async def test_idempotent_data_ingestion_and_caching():
    mock_provider = MockDataProvider()
    service = DataIngestionService(default_provider=mock_provider)

    async with async_session_factory() as session:
        stock = await service.get_or_create_stock(session, "INFY.NS")

        # 1st ingestion
        df1 = await service.get_or_fetch_market_data(
            session=session,
            symbol="INFY.NS",
            force_refresh=True,
            provider=mock_provider,
        )
        assert len(df1) == 60

        cnt1 = len((await session.execute(
            select(MarketData).where(MarketData.stock_id == stock.id)
        )).scalars().all())
        assert cnt1 >= 60

        # 2nd ingestion (should read from cache and insert 0 duplicates)
        df2 = await service.get_or_fetch_market_data(
            session=session,
            symbol="INFY.NS",
            force_refresh=False,
            provider=mock_provider,
        )
        assert len(df2) >= 60

        cnt2 = len((await session.execute(
            select(MarketData).where(MarketData.stock_id == stock.id)
        )).scalars().all())
        assert cnt2 == cnt1

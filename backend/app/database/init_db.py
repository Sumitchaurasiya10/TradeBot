from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.core.security import get_password_hash
from backend.app.database.base import Base
from backend.app.database.session import async_session_factory, engine
from backend.app.models import PaperAccount, Stock, User


async def init_db() -> None:
    """
    Creates all database tables and seeds initial stock universe, demo user, and paper account.
    """
    logger.info("Initializing database schema...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables verified/created successfully.")

    async with async_session_factory() as session:
        # 1. Seed Stocks
        default_stocks = [
            ("RELIANCE.NS", "Reliance Industries Limited", "Energy & Conglomerate"),
            ("TCS.NS", "Tata Consultancy Services Limited", "Information Technology"),
            ("INFY.NS", "Infosys Limited", "Information Technology"),
            ("HDFCBANK.NS", "HDFC Bank Limited", "Banking & Financials"),
            ("ICICIBANK.NS", "ICICI Bank Limited", "Banking & Financials"),
            ("SBIN.NS", "State Bank of India", "Banking & Financials"),
            ("ITC.NS", "ITC Limited", "FMCG"),
            ("LT.NS", "Larsen & Toubro Limited", "Engineering & Infrastructure"),
        ]

        for symbol, name, sector in default_stocks:
            stmt = select(Stock).where(Stock.symbol == symbol)
            result = await session.execute(stmt)
            existing_stock = result.scalars().first()
            if not existing_stock:
                stock = Stock(symbol=symbol, company_name=name, sector=sector, is_active=True)
                session.add(stock)

        # 2. Seed Default Paper Account
        account_stmt = select(PaperAccount).where(PaperAccount.account_name == "Default Paper Account")
        account_res = await session.execute(account_stmt)
        existing_account = account_res.scalars().first()

        if not existing_account:
            initial_cap = settings.DEFAULT_INITIAL_CAPITAL
            account = PaperAccount(
                account_name="Default Paper Account",
                initial_balance=initial_cap,
                current_cash=initial_cap,
                currency="INR",
            )
            session.add(account)

        # 3. Seed Default Demo User
        user_stmt = select(User).where(User.email == "demo@tradebot.in")
        user_res = await session.execute(user_stmt)
        existing_user = user_res.scalars().first()

        if not existing_user:
            demo_user = User(
                email="demo@tradebot.in",
                full_name="Demo Trader",
                hashed_password=get_password_hash("password123"),
                is_active=True,
                role="trader",
            )
            session.add(demo_user)

        await session.commit()
        logger.info("Database seeding completed.")


if __name__ == "__main__":
    import asyncio
    asyncio.run(init_db())

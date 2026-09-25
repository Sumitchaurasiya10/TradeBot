from datetime import datetime
import pytz
from fastapi import APIRouter
from backend.app.core.config import settings
from backend.app.schemas.bot import BotStatusResponse

router = APIRouter()


@router.get("/status", response_model=BotStatusResponse)
async def get_bot_status():
    """
    Returns the real-time operational status of the bot, environment parameters,
    market hours state in IST, and transparency notices regarding data feeds.
    """
    tz = pytz.timezone(settings.MARKET_TIMEZONE)
    now_ist = datetime.now(tz)

    # Indian Market Hours: 09:15 to 15:30 IST, Monday-Friday
    is_weekday = now_ist.weekday() < 5
    current_time_str = now_ist.strftime("%H:%M")
    is_open = is_weekday and (settings.MARKET_OPEN_TIME <= current_time_str <= settings.MARKET_CLOSE_TIME)

    return BotStatusResponse(
        status="ONLINE",
        environment=settings.ENVIRONMENT,
        paper_trading_mode=True,
        real_money_trading=False,
        data_provider="yfinance",
        data_provider_notice=(
            "Unofficial Yahoo Finance public interface. Data subject to rate limits, "
            "exchange delays (~15m for intraday), and quality constraints. Designed for simulation and educational review."
        ),
        market_timezone=settings.MARKET_TIMEZONE,
        market_hours=f"{settings.MARKET_OPEN_TIME} - {settings.MARKET_CLOSE_TIME} IST (Mon-Fri)",
        is_market_open=is_open,
        supported_symbols=settings.SUPPORTED_SYMBOLS,
    )

from datetime import datetime, time, timedelta
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
import pytz

IST = pytz.timezone("Asia/Kolkata")


class MarketSession(str, Enum):
    PRE_OPEN = "PRE-OPEN"
    MARKET_OPEN = "MARKET OPEN"
    POST_MARKET = "POST-MARKET"
    MARKET_CLOSED = "MARKET CLOSED"
    DATA_UNAVAILABLE = "DATA UNAVAILABLE"


class MarketSessionStatus(BaseModel):
    session: MarketSession
    is_open: bool
    current_time_ist: str
    session_hours: str = "09:15 - 15:30 IST (Mon-Fri)"
    timezone: str = "Asia/Kolkata"
    next_open_time: Optional[str] = None
    next_close_time: Optional[str] = None
    message: str


class MarketStatusService:
    """
    Evaluates official NSE equity and derivative trading session states.
    All calculations are strictly localized to 'Asia/Kolkata' timezone.
    """

    PRE_OPEN_START = time(9, 0)
    MARKET_OPEN = time(9, 15)
    MARKET_CLOSE = time(15, 30)
    POST_MARKET_CLOSE = time(16, 0)

    @classmethod
    def get_status(cls, check_time: Optional[datetime] = None) -> MarketSessionStatus:
        if check_time is None:
            now = datetime.now(IST)
        else:
            if check_time.tzinfo is None:
                now = IST.localize(check_time)
            else:
                now = check_time.astimezone(IST)

        curr_time = now.time()
        weekday = now.weekday()  # Monday = 0, Sunday = 6
        is_weekend = weekday >= 5

        time_str = now.strftime("%Y-%m-%d %H:%M:%S IST")

        # Weekend Check
        if is_weekend:
            # Next open is Monday 09:15 IST
            days_to_monday = 7 - weekday
            next_open = (now + timedelta(days=days_to_monday)).replace(hour=9, minute=15, second=0, microsecond=0)
            return MarketSessionStatus(
                session=MarketSession.MARKET_CLOSED,
                is_open=False,
                current_time_ist=time_str,
                next_open_time=next_open.strftime("%Y-%m-%d %H:%M:%S IST"),
                message="Weekend: Indian markets closed until Monday 09:15 IST",
            )

        # Pre-Open (09:00 - 09:15)
        if cls.PRE_OPEN_START <= curr_time < cls.MARKET_OPEN:
            next_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
            return MarketSessionStatus(
                session=MarketSession.PRE_OPEN,
                is_open=False,
                current_time_ist=time_str,
                next_open_time=now.replace(hour=9, minute=15, second=0, microsecond=0).strftime("%Y-%m-%d %H:%M:%S IST"),
                next_close_time=next_close.strftime("%Y-%m-%d %H:%M:%S IST"),
                message="Pre-market price discovery session (Order collection & matching)",
            )

        # Regular Trading Hours (09:15 - 15:30)
        if cls.MARKET_OPEN <= curr_time < cls.MARKET_CLOSE:
            next_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
            return MarketSessionStatus(
                session=MarketSession.MARKET_OPEN,
                is_open=True,
                current_time_ist=time_str,
                next_close_time=next_close.strftime("%Y-%m-%d %H:%M:%S IST"),
                message="Live continuous trading session active on NSE & BSE",
            )

        # Post-Market (15:30 - 16:00)
        if cls.MARKET_CLOSE <= curr_time < cls.POST_MARKET_CLOSE:
            # Next open is tomorrow or Monday
            days_ahead = 3 if weekday == 4 else 1
            next_open = (now + timedelta(days=days_ahead)).replace(hour=9, minute=15, second=0, microsecond=0)
            return MarketSessionStatus(
                session=MarketSession.POST_MARKET,
                is_open=False,
                current_time_ist=time_str,
                next_open_time=next_open.strftime("%Y-%m-%d %H:%M:%S IST"),
                message="Post-market closing price calculation & settlement session",
            )

        # Evening / Early Morning Closed
        days_ahead = 1 if curr_time >= cls.POST_MARKET_CLOSE else 0
        if weekday == 4 and curr_time >= cls.POST_MARKET_CLOSE:
            days_ahead = 3
        next_open = (now + timedelta(days=days_ahead)).replace(hour=9, minute=15, second=0, microsecond=0)

        return MarketSessionStatus(
            session=MarketSession.MARKET_CLOSED,
            is_open=False,
            current_time_ist=time_str,
            next_open_time=next_open.strftime("%Y-%m-%d %H:%M:%S IST"),
            message="Markets are closed. Next regular trading session at 09:15 IST",
        )
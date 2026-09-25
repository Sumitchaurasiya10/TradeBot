from typing import List
from pydantic import BaseModel


class BotStatusResponse(BaseModel):
    status: str  # "ONLINE", "DEGRADED", "OFFLINE"
    environment: str
    paper_trading_mode: bool  # strictly True
    real_money_trading: bool  # strictly False
    data_provider: str
    data_provider_notice: str
    market_timezone: str
    market_hours: str
    is_market_open: bool
    supported_symbols: List[str]

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Annotated, List, Optional
from pydantic import BaseModel, ConfigDict, Field, PlainSerializer

# Serializes Decimal to JSON float while preserving Decimal in Python
DecimalNum = Annotated[
    Decimal,
    PlainSerializer(lambda x: float(x) if x is not None else None, return_type=float),
]


class DataStatus(str, Enum):
    LIVE = "LIVE"
    DELAYED = "DELAYED"
    HISTORICAL = "HISTORICAL"
    SIMULATED = "SIMULATED"
    DEMO_DATA = "DEMO DATA"
    STALE = "STALE"
    UNAVAILABLE = "UNAVAILABLE"


class AssetType(str, Enum):
    EQUITY = "EQUITY"
    INDEX = "INDEX"
    FUTURE = "FUTURE"
    OPTION = "OPTION"


class InstrumentType(str, Enum):
    EQ = "EQ"
    FUTSTK = "FUTSTK"
    FUTIDX = "FUTIDX"
    OPTIDX = "OPTIDX"
    OPTSTK = "OPTSTK"


class OptionType(str, Enum):
    CE = "CE"
    PE = "PE"


class Quote(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    symbol: str = Field(..., description="Trading ticker symbol (e.g. RELIANCE, TCS)")
    exchange: str = Field(default="NSE", description="Exchange: NSE or BSE")
    asset_type: AssetType = Field(default=AssetType.EQUITY, description="Asset classification")
    timestamp: datetime = Field(..., description="Timestamp of the quote (Asia/Kolkata aware)")
    last_price: DecimalNum = Field(..., description="Last Traded Price (LTP)")
    open: Optional[DecimalNum] = Field(default=None, description="Day opening price")
    high: Optional[DecimalNum] = Field(default=None, description="Day high price")
    low: Optional[DecimalNum] = Field(default=None, description="Day low price")
    previous_close: Optional[DecimalNum] = Field(default=None, description="Previous session closing price")
    change: Optional[DecimalNum] = Field(default=None, description="Absolute change from previous close")
    change_percent: Optional[DecimalNum] = Field(default=None, description="Percentage change from previous close")
    volume: int = Field(default=0, description="Total traded volume for the session")
    bid_price: Optional[DecimalNum] = Field(default=None, description="Top buy bid price")
    ask_price: Optional[DecimalNum] = Field(default=None, description="Top sell ask price")
    bid_quantity: Optional[int] = Field(default=None, description="Quantity available at top bid")
    ask_quantity: Optional[int] = Field(default=None, description="Quantity available at top ask")
    data_status: DataStatus = Field(default=DataStatus.LIVE, description="Transparency tag for data feed")


class IndexQuote(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    symbol: str = Field(..., description="Index name: NIFTY 50, SENSEX, BANK NIFTY")
    exchange: str = Field(default="NSE", description="Exchange: NSE or BSE")
    timestamp: datetime = Field(..., description="Timestamp of the index value")
    last_price: DecimalNum = Field(..., description="Current index points")
    open: Optional[DecimalNum] = Field(default=None, description="Opening index value")
    high: Optional[DecimalNum] = Field(default=None, description="Day high index value")
    low: Optional[DecimalNum] = Field(default=None, description="Day low index value")
    previous_close: Optional[DecimalNum] = Field(default=None, description="Previous session close")
    change: Optional[DecimalNum] = Field(default=None, description="Point change")
    change_percent: Optional[DecimalNum] = Field(default=None, description="Percentage change")
    data_status: DataStatus = Field(default=DataStatus.LIVE, description="Transparency tag")


class FNOQuote(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    underlying: str = Field(..., description="Underlying equity or index symbol (e.g. NIFTY, TCS)")
    symbol: str = Field(..., description="Full contract symbol (e.g. NIFTY24OCT25000CE)")
    exchange: str = Field(default="NSE", description="Exchange")
    instrument_type: InstrumentType = Field(..., description="F&O Instrument classification")
    expiry: str = Field(..., description="Contract expiry date (YYYY-MM-DD)")
    strike_price: Optional[DecimalNum] = Field(default=None, description="Strike price for options")
    option_type: Optional[OptionType] = Field(default=None, description="CE (Call) or PE (Put)")
    timestamp: datetime = Field(..., description="Quote timestamp")
    last_price: DecimalNum = Field(..., description="Last Traded Price (LTP)")
    open: Optional[DecimalNum] = Field(default=None)
    high: Optional[DecimalNum] = Field(default=None)
    low: Optional[DecimalNum] = Field(default=None)
    previous_close: Optional[DecimalNum] = Field(default=None)
    change: Optional[DecimalNum] = Field(default=None, description="Absolute price change")
    change_percent: Optional[DecimalNum] = Field(default=None, description="Percentage change")
    volume: int = Field(default=0, description="Contracts traded volume")
    open_interest: int = Field(default=0, description="Open Interest (OI) in contracts/shares")
    change_in_oi: int = Field(default=0, description="Day change in Open Interest")
    bid_price: Optional[DecimalNum] = Field(default=None)
    ask_price: Optional[DecimalNum] = Field(default=None)
    bid_quantity: Optional[int] = Field(default=None)
    ask_quantity: Optional[int] = Field(default=None)
    implied_volatility: Optional[DecimalNum] = Field(default=None, description="IV in percentage")
    data_status: DataStatus = Field(default=DataStatus.LIVE)


class OptionChainStrikeRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    strike_price: DecimalNum = Field(..., description="Option strike price")
    call: Optional[FNOQuote] = Field(default=None, description="Call Option (CE) data")
    put: Optional[FNOQuote] = Field(default=None, description="Put Option (PE) data")


class OptionChainResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    underlying: str = Field(..., description="Underlying asset (NIFTY, BANK NIFTY, TCS)")
    underlying_price: DecimalNum = Field(..., description="Current spot LTP of underlying")
    expiry: str = Field(..., description="Selected expiry date")
    available_expiries: List[str] = Field(default_factory=list, description="All available active expiry dates")
    timestamp: datetime = Field(..., description="Data snapshot timestamp")
    data_status: DataStatus = Field(default=DataStatus.LIVE, description="Transparency tag")
    strikes: List[OptionChainStrikeRow] = Field(default_factory=list, description="Strikes with Call & Put quotes")
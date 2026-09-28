from fastapi import APIRouter
from backend.app.api.v1.endpoints import (
    auth,
    backtest,
    bot,
    fno,
    market,
    paper,
    stocks,
    strategy,
    ws,
)

api_router = APIRouter()

api_router.include_router(auth.router, tags=["Authentication"])
api_router.include_router(ws.router, tags=["Live WebSocket Streaming"])
api_router.include_router(market.router, prefix="/market", tags=["Market Data & Indices"])
api_router.include_router(fno.router, prefix="/fno", tags=["Futures & Options (F&O)"])
api_router.include_router(stocks.router, prefix="/stocks", tags=["Stocks & Market Data"])
api_router.include_router(strategy.router, prefix="/strategy", tags=["Trading Strategy"])
api_router.include_router(backtest.router, prefix="/backtest", tags=["Backtesting"])
api_router.include_router(paper.router, prefix="/paper", tags=["Paper Trading"])
api_router.include_router(bot.router, prefix="/bot", tags=["Bot Operations"])

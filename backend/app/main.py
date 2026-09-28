import os
import sys

# Ensure project root is in sys.path so 'backend.app' works when running from inside backend/
_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_root_dir = os.path.dirname(_backend_dir)
for _p in (_root_dir, _backend_dir):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.api.v1.router import api_router
from backend.app.core.config import settings
from backend.app.core.logging import logger, setup_logging
from backend.app.database.init_db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_logging()
    logger.info(f"Starting {settings.PROJECT_NAME}...")
    await init_db()
    logger.info("Application startup completed successfully.")
    yield
    # Shutdown
    logger.info("Application shutdown.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "Educational & Technical Interview Portfolio: Indian Equity Market Paper Trading Bot. "
        "Strictly simulated paper trading with zero live broker execution. Features explainable "
        "rule-based EMA+RSI+Volume strategies, zero look-ahead bias backtesting, and realistic Indian "
        "transaction cost modeling."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API v1 Router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Health"])
async def root():
    return {
        "project": settings.PROJECT_NAME,
        "status": "HEALTHY",
        "mode": "PAPER_TRADING_ONLY",
        "disclaimer": "Paper Trading Only. No real money or real trades.",
        "docs": "/docs",
    }
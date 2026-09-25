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
        "Strictly simulated trading with explainable technical indicators (EMA + RSI + Volume), "
        "chronological zero-lookahead backtesting, and normalized database caching."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS configuration for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API v1 router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Health"])
async def root():
    return {
        "project": settings.PROJECT_NAME,
        "status": "HEALTHY",
        "api_docs": "/docs",
        "api_v1_prefix": settings.API_V1_STR,
        "disclaimer": "Paper/simulated trading only. Not financial advice.",
    }

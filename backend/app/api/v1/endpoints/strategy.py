from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.database.session import get_db
from backend.app.schemas.strategy import SignalRequest, SignalResponse
from backend.app.services.data_ingestion import DataIngestionService
from backend.app.services.data_validator import DataValidationError, DataValidator
from backend.app.services.market_data import get_market_data_provider
from backend.app.strategies.ema_rsi_volume import EMARsiVolumeStrategy

router = APIRouter()
ingestion_service = DataIngestionService()


@router.post("/signal", response_model=SignalResponse)
async def evaluate_signal(request: SignalRequest, db: AsyncSession = Depends(get_db)):
    """
    Evaluates current market data for an Indian stock against the configurable
    EMA Crossover + RSI + Volume Confirmation strategy.
    Returns structured signal (BUY / SELL / HOLD), reason, and indicator values.
    """
    if request.fast_ema_period >= request.slow_ema_period:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"fast_ema_period ({request.fast_ema_period}) must be strictly less than slow_ema_period ({request.slow_ema_period})",
        )

    try:
        clean_symbol = DataValidator.validate_symbol(request.symbol)
        df = await ingestion_service.get_or_fetch_market_data(session=db, symbol=clean_symbol)

        strategy = EMARsiVolumeStrategy(
            fast_ema_period=request.fast_ema_period,
            slow_ema_period=request.slow_ema_period,
            rsi_period=request.rsi_period,
            rsi_entry_threshold=request.rsi_entry_threshold,
            rsi_max_threshold=request.rsi_max_threshold,
            rsi_exit_threshold=request.rsi_exit_threshold,
            volume_ma_period=request.volume_ma_period,
            volume_multiplier=request.volume_multiplier,
        )

        signal_obj = strategy.generate_signal(df, clean_symbol)

        return SignalResponse(
            signal=signal_obj.signal.value,
            timestamp=signal_obj.timestamp,
            symbol=signal_obj.symbol,
            reason=signal_obj.reason,
            indicators=signal_obj.indicators,
            parameters=strategy.get_parameters(),
        )

    except DataValidationError as dve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(dve))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error evaluating strategy signal for '{request.symbol}': {str(e)}",
        )


@router.get("/live-signal/{symbol}", response_model=SignalResponse, summary="Get Live Real-Time Signal for Stock")
async def get_live_strategy_signal(
    symbol: str,
    fast_ema: int = 9,
    slow_ema: int = 21,
    rsi_period: int = 14,
    rsi_entry_threshold: float = 50.0,
    rsi_max_threshold: float = 85.0,
    rsi_exit_threshold: float = 45.0,
    volume_ma_period: int = 20,
    volume_multiplier: float = 1.0,
    provider=Depends(get_market_data_provider),
):
    """
    Evaluates real-time / streaming market data against the rule-based
    EMA + RSI + Volume Confirmation strategy.
    """
    if fast_ema >= slow_ema:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"fast_ema ({fast_ema}) must be strictly less than slow_ema ({slow_ema})",
        )

    from backend.app.services.live_strategy_evaluator import LiveStrategyEvaluator

    return await LiveStrategyEvaluator.evaluate_live_signal(
        symbol=symbol,
        provider=provider,
        fast_ema=fast_ema,
        slow_ema=slow_ema,
        rsi_period=rsi_period,
        rsi_entry_threshold=rsi_entry_threshold,
        rsi_max_threshold=rsi_max_threshold,
        rsi_exit_threshold=rsi_exit_threshold,
        volume_ma_period=volume_ma_period,
        volume_multiplier=volume_multiplier,
    )

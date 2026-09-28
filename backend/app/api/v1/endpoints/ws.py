import asyncio
from datetime import datetime
import json
from typing import Dict, List, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import pytz

from backend.app.core.logging import logger
from backend.app.schemas.market import DataStatus
from backend.app.services.market_cache import market_cache
from backend.app.services.market_data import get_market_data_provider
from backend.app.services.market_status import MarketStatusService

IST = pytz.timezone("Asia/Kolkata")
router = APIRouter()


class WebSocketConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.subscriptions: Dict[WebSocket, Dict] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        self.subscriptions[websocket] = {
            "symbols": {"RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK"},
            "include_indices": True,
        }

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        self.subscriptions.pop(websocket, None)

    def update_subscriptions(self, websocket: WebSocket, symbols: List[str], include_indices: bool):
        if websocket in self.subscriptions:
            clean_syms = {s.upper().replace(".NS", "").strip() for s in symbols}
            self.subscriptions[websocket]["symbols"] = clean_syms
            self.subscriptions[websocket]["include_indices"] = include_indices


manager = WebSocketConnectionManager()


@router.websocket("/ws/market")
async def websocket_market_feed(websocket: WebSocket):
    """
    Real-time streaming WebSocket endpoint for the Next.js frontend.
    Pushes continuous index updates, watchlist quotes, and market session heartbeats.
    """
    await manager.connect(websocket)
    provider = get_market_data_provider()

    # Background task to send periodic streaming ticks
    async def push_updates():
        try:
            while True:
                sub_config = manager.subscriptions.get(websocket)
                if not sub_config:
                    break

                # 1. Market Status
                status = MarketStatusService.get_status()
                await websocket.send_text(
                    json.dumps({
                        "type": "market_status",
                        "data": status.model_dump(),
                        "timestamp": datetime.now(IST).strftime("%H:%M:%S IST"),
                    })
                )

                # 2. Indices
                if sub_config.get("include_indices", True):
                    indices = await provider.get_indices_quotes()
                    await market_cache.set_indices_quotes(indices)
                    await websocket.send_text(
                        json.dumps({
                            "type": "indices_update",
                            "data": [idx.model_dump(mode="json") for idx in indices],
                            "timestamp": datetime.now(IST).strftime("%H:%M:%S IST"),
                        })
                    )

                # 3. Subscribed Quotes
                symbols = list(sub_config.get("symbols", []))
                if symbols:
                    quotes = await provider.get_quotes(symbols)
                    await market_cache.set_quotes(quotes)
                    await websocket.send_text(
                        json.dumps({
                            "type": "quotes_update",
                            "data": [q.model_dump(mode="json") for q in quotes],
                            "timestamp": datetime.now(IST).strftime("%H:%M:%S IST"),
                        })
                    )

                # Stream tick interval: 3 seconds
                await asyncio.sleep(3)
        except (WebSocketDisconnect, asyncio.CancelledError):
            pass
        except Exception as e:
            logger.warning(f"WebSocket client loop error: {e}")

    stream_task = asyncio.create_task(push_updates())

    try:
        while True:
            # Listen for client commands (subscribe, ping)
            data_text = await websocket.receive_text()
            try:
                msg = json.loads(data_text)
                action = msg.get("action")
                if action == "subscribe":
                    syms = msg.get("symbols", [])
                    inc_indices = msg.get("include_indices", True)
                    manager.update_subscriptions(websocket, syms, inc_indices)
                    await websocket.send_text(
                        json.dumps({"type": "subscribed", "symbols": syms, "status": "OK"})
                    )
                elif action == "ping":
                    await websocket.send_text(
                        json.dumps({"type": "pong", "timestamp": datetime.now(IST).isoformat()})
                    )
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        stream_task.cancel()
    except Exception as e:
        logger.warning(f"WebSocket listener error: {e}")
        manager.disconnect(websocket)
        stream_task.cancel()
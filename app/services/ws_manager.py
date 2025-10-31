import json
from typing import List
from fastapi import WebSocket
from app.common.logger import logger

class WSManager:
    def __init__(self):
        self.connections: List[WebSocket] = []

    async def startup(self):
        logger.info("[WS] Manager startup")

    async def shutdown(self):
        logger.info("[WS] Manager shutdown")
        for ws in list(self.connections):
            try:
                await ws.close()
            except Exception:
                pass
        self.connections.clear()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.connections.append(websocket)
        logger.info(f"[WS] Connection accepted. Total: {len(self.connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.connections:
            self.connections.remove(websocket)
            logger.info(f"[WS] Disconnected. Total: {len(self.connections)}")

    async def broadcast_game_update(self, game_id: str, payload: dict):
        message = json.dumps({"game_id": game_id, "payload": payload}, ensure_ascii=False)
        for ws in list(self.connections):
            try:
                await ws.send_text(message)
            except Exception:
                try:
                    await ws.close()
                except Exception:
                    pass
                self.disconnect(ws)

ws_manager = WSManager()

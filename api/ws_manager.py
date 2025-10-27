import asyncio
from typing import Dict, List, Optional
from fastapi import WebSocket
import logging
import json

logger = logging.getLogger("ws_manager")
logger.setLevel(logging.INFO)

class Connection:
    def __init__(self, websocket: WebSocket, player_id: Optional[str] = None):
        self.websocket = websocket
        self.player_id = player_id

class WSManager:
    def __init__(self):
        # map game_id -> list[Connection]
        self.connections: Dict[str, List[Connection]] = {}
        self.lock = asyncio.Lock()

    async def connect(self, game_id: str, websocket: WebSocket, player_id: Optional[str] = None):
        """
        Добавить подключение. Рекомендуется при открытии WS клиентом отправлять JSON { "player_id": "p1" } 
        или передавать player_id в URL/Query.
        """
        await websocket.accept()
        conn = Connection(websocket, player_id)
        async with self.lock:
            self.connections.setdefault(game_id, []).append(conn)
        logger.info("WS CONNECT %s player=%s", game_id, player_id)

    async def disconnect(self, game_id: str, websocket: WebSocket):
        async with self.lock:
            conns = self.connections.get(game_id, [])
            for c in list(conns):
                if c.websocket == websocket:
                    conns.remove(c)
                    logger.info("WS DISCONNECT %s player=%s", game_id, c.player_id)
                    break

    async def broadcast(self, game_id: str, message: dict):
        """
        Широковещательная отправка всем подключённым к партии.
        """
        conns = list(self.connections.get(game_id, []))
        if not conns:
            return
        data = message
        for c in conns:
            try:
                await c.websocket.send_json(data)
            except Exception:
                # если отправка упала — удаляем
                await self.disconnect(game_id, c.websocket)

    async def send_to_player(self, game_id: str, player_id: str, message: dict):
        """
        Отправить сообщение определённому игроку (если он подключён).
        """
        conns = list(self.connections.get(game_id, []))
        for c in conns:
            if c.player_id == player_id:
                try:
                    await c.websocket.send_json(message)
                    return True
                except Exception:
                    await self.disconnect(game_id, c.websocket)
                    return False
        return False

    async def send_to_connection(self, websocket: WebSocket, message: dict):
        try:
            await websocket.send_json(message)
            return True
        except Exception:
            return False

    async def ping_all(self):
        """
        Простой метод для пинга всех подключений (можно запускать через фон.таски).
        """
        for game_id, conns in list(self.connections.items()):
            for c in list(conns):
                try:
                    await c.websocket.send_json({"event": "ping"})
                except Exception:
                    await self.disconnect(game_id, c.websocket)

# глобальный менеджер, чтобы использовать из сервисов/роутов
ws_manager = WSManager()

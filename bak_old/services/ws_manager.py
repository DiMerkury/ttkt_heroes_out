from typing import Dict, List
from fastapi import WebSocket

class WSManager:
    def __init__(self):
        self.connections: Dict[str, Dict[str, WebSocket]] = {}

    async def connect(self, websocket: WebSocket, game_id: str, player_id: str):
        await websocket.accept()
        self.connections.setdefault(game_id, {})[player_id] = websocket

    async def disconnect(self, game_id: str, player_id: str):
        self.connections.get(game_id, {}).pop(player_id, None)

    async def send_to_player(self, player_id: str, message: dict):
        for games in self.connections.values():
            if player_id in games:
                await games[player_id].send_json(message)

    async def broadcast(self, game_id: str, message: dict):
        for ws in self.connections.get(game_id, {}).values():
            await ws.send_json(message)

    async def handle_message(self, game_id: str, player_id: str, data: str):
        print(f"[WS] from {player_id}@{game_id}: {data}")

from fastapi import FastAPI, WebSocket
from api_app.routes.game_routes import router as game_router
from services.ws_manager import WSManager
from common.redis_store import RedisStore

app = FastAPI(title="Dungeon Lords Online")

# Инициализация зависимостей
store = RedisStore()
ws_manager = WSManager()

# Подключаем маршруты
app.include_router(game_router)

@app.websocket("/ws/{game_id}/{player_id}")
async def websocket_endpoint(websocket: WebSocket, game_id: str, player_id: str):
    await ws_manager.connect(websocket, game_id, player_id)
    try:
        while True:
            data = await websocket.receive_text()
            await ws_manager.handle_message(game_id, player_id, data)
    except Exception:
        await ws_manager.disconnect(game_id, player_id)

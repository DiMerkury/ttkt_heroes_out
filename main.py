from fastapi import FastAPI, WebSocket
from api.routes.routes_game import router as game_router
from api.ws_manager import ws_manager

app = FastAPI(title="KTHO Backend - Full Backup")

app.include_router(game_router, prefix="/game", tags=["Game"])

@app.on_event("startup")
async def startup():
    print("App starting...")

@app.websocket("/ws/{game_id}")
async def websocket_endpoint(websocket: WebSocket, game_id: str):
    await websocket.accept()
    try:
        # ожидаем приветственное сообщение, где клиент может прислать player_id
        raw = await websocket.receive_text()
        try:
            data = json.loads(raw)
            player_id = data.get("player_id")
        except Exception:
            player_id = None
        await ws_manager.connect(game_id, websocket, player_id=player_id)

        # основной loop
        while True:
            msg = await websocket.receive_text()
            # здесь можно обрабатывать входящие WS-сообщения (чат, ready, discard выбор и т.п.)
    except Exception:
        await ws_manager.disconnect(game_id, websocket)

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from redis.asyncio import Redis
from services.game_service import GameService
from common.redis_manager import RedisStorage
from services.game_initializer import GameInitializer
from api.ws_manager import ws_manager

router = APIRouter()
storage = RedisStorage()
game_service = GameService(storage, ws_manager)

class StartRequest(BaseModel):
    scenario_id: str = "scenario_01"
    players: list[str] = ["p1"]
    difficulty: str = "normal"

@router.post("/start")
async def start_game(req: StartRequest):
    state = await game_service.start_game(req.scenario_id, req.players, req.difficulty)
    return state

@router.get("/{game_id}/state")
async def get_state(game_id: str):
    state = await game_service.get_state(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Game not found")
    return state

@router.post("/{game_id}/end_turn")
async def end_turn(game_id: str):
    state = await game_service.end_turn(game_id)
    return state

@router.post("/{game_id}/discard")
async def discard_card(game_id: str, payload: dict):
    player_id = payload.get("player_id")
    card_id = payload.get("card_id")
    if not player_id or not card_id:
        raise HTTPException(400, "player_id and card_id required")
    res = await game_service.player_discard(game_id, player_id, card_id)
    return res

@router.post("/new")
async def create_new_game(
    player_names: list[str],
    difficulty: str = "family",
    redis: Redis = Depends(),
):
    """
    Создаёт новую игру и возвращает стартовое состояние.
    """
    game_id = f"game_{hash(tuple(player_names)) % 10000}"

    initializer = GameInitializer(redis)
    state = await initializer.create_new_game(game_id, player_names, difficulty)

    return {"game_id": game_id, "state": state.to_dict()}

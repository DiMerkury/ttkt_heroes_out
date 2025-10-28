from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from common.dependencies import get_redis
from common.redis_manager import RedisStorage
from services.game_service import GameService
from api.ws_manager import ws_manager


router = APIRouter()


# ----------------------------
# Схемы запросов и ответов
# ----------------------------

class StartRequest(BaseModel):
    scenario_id: str = Field("scenario_01", description="ID сценария")
    players: list[str] = Field(["p1"], description="Список имён игроков")
    difficulty: str = Field("normal", description="Уровень сложности ('family'|'normal'|'hard')")


class CreateNewGameRequest(BaseModel):
    game_id: str = Field(..., description="ID новой партии")
    player_names: list[str] = Field(..., description="Список имён игроков")
    difficulty: Optional[str] = Field("family", description="Уровень сложности")


# ----------------------------
# Маршруты
# ----------------------------

@router.post("/start")
async def start_game(
    req: StartRequest,
    redis: RedisStorage = Depends(get_redis),
):
    """
    Создаёт и запускает новую игру на основе сценария.
    """
    game_service = GameService(redis, ws_manager)
    state = await game_service.start_game(req.scenario_id, req.players, req.difficulty)
    return state


@router.get("/{game_id}/state")
async def get_state(
    game_id: str,
    redis: RedisStorage = Depends(get_redis),
):
    """
    Возвращает текущее состояние игры из Redis.
    """
    game_service = GameService(redis, ws_manager)
    state = await game_service.get_state(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Game not found")
    return state


@router.post("/{game_id}/end_turn")
async def end_turn(
    game_id: str,
    redis: RedisStorage = Depends(get_redis),
):
    """
    Завершает текущий ход игрока и запускает действия героев.
    """
    game_service = GameService(redis, ws_manager)
    state = await game_service.end_turn(game_id)
    return state


@router.post("/{game_id}/discard")
async def discard_card(
    game_id: str,
    payload: dict,
    redis: RedisStorage = Depends(get_redis),
):
    """
    Сбрасывает карту из руки игрока.
    """
    player_id = payload.get("player_id")
    card_id = payload.get("card_id")
    if not player_id or not card_id:
        raise HTTPException(status_code=400, detail="player_id and card_id required")

    game_service = GameService(redis, ws_manager)
    res = await game_service.player_discard(game_id, player_id, card_id)
    return res


@router.post("/new")
async def create_new_game(
    req: CreateNewGameRequest,
    redis: RedisStorage = Depends(get_redis),
):
    """
    Создаёт новую игру и сохраняет стартовое состояние.
    """
    game_service = GameService(redis, ws_manager)
    state = await game_service.create_game(req.game_id, req.player_names, req.difficulty)
    return {"game_id": req.game_id, "state": state.to_dict()}

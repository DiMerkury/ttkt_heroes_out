from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from app.common.dependencies import get_redis
from app.common.redis_manager import RedisStorage
from app.services.game_service import GameService
from app.services.ws_manager import ws_manager

router = APIRouter(tags=["game"])


class CreateNewGameRequest(BaseModel):
    game_id: str = Field(..., description="ID новой партии")
    player_names: List[str] = Field(..., description="Список имён игроков")
    scenario_id: str = Field(..., description="ID сценария")
    difficulty: Optional[str] = Field("family", description="Уровень сложности")


@router.post("/new")
async def create_new_game(req: CreateNewGameRequest, redis: RedisStorage = Depends(get_redis)):
    service = GameService(redis)
    state = await service.create_game(req.game_id, req.player_names, req.scenario_id, req.difficulty)
    # notify via ws (if clients subscribed)
    await ws_manager.broadcast_game_update(state.id, {"event": "game_created", "game_id": state.id})
    return {"game_id": state.id, "state": state.to_dict()}


@router.get("/{game_id}/state")
async def get_state(game_id: str, redis: RedisStorage = Depends(get_redis)):
    service = GameService(redis)
    state = await service.get_state(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Game not found")
    return state


@router.post("/{game_id}/end_turn")
async def end_turn(game_id: str, redis: RedisStorage = Depends(get_redis)):
    service = GameService(redis)
    state = await service.start_next_wave(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Game not found")
    await ws_manager.broadcast_game_update(game_id, {"event": "wave_completed", "game_id": game_id, "wave": state.wave})
    return state


@router.post("/{game_id}/treasure/{tier}")
async def open_treasure(game_id: str, tier: int, redis: RedisStorage = Depends(get_redis)):
    service = GameService(redis)
    state = await service.load_state(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Game not found")
    # apply effects directly (admin/manual trigger)
    await service.rule_engine.apply_treasure_effect(state, str(tier))
    await service.save_state(game_id, state)
    await ws_manager.broadcast_game_update(game_id, {"event": "treasure_opened", "tier": tier})
    return {"status": "ok"}

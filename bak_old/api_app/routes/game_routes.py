from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from services.game_service import GameService
from services.ws_manager import WSManager
from common.redis_store import RedisStore
from services.event_logger import EventLogger

router = APIRouter(prefix="/game", tags=["Game"])

store = RedisStore()
ws_manager = WSManager()
logger = EventLogger(store, ws_manager)
game_service = GameService(store, ws_manager, logger)


# --- Модели запросов ---
class StartGameModel(BaseModel):
    scenario_id: str
    players: List[str]
    difficulty: str = "family"


class StartGameResponse(BaseModel):
    game_id: str
    status: str
    difficulty: str
    scenario_id: str
    players: List[str]


@router.post("/start", response_model=StartGameResponse)
async def start_game(payload: StartGameModel):
    scenario = await game_service.load_scenario(payload.scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")

    state = await game_service.init_game_state(
        scenario=payload.scenario_id,
        players=payload.players,
        difficulty=payload.difficulty,
    )

    await game_service.save_state(state["id"], state)
    await ws_manager.broadcast(state["id"], {"event": "game_started", "game": state})

    return StartGameResponse(
        game_id=state["id"],
        status=state["status"],
        difficulty=payload.difficulty,
        scenario_id=payload.scenario_id,
        players=payload.players,
    )


@router.get("/{game_id}/state")
async def get_game_state(game_id: str):
    state = await game_service.load_state(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Game not found")
    return state


class DiscardCardRequest(BaseModel):
    player_id: str
    card_id: str


@router.post("/{game_id}/discard")
async def discard_card(game_id: str, data: DiscardCardRequest):
    state = await game_service.load_state(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Game not found")

    player = next((p for p in state["players"] if p["id"] == data.player_id), None)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    if data.card_id not in player["hand"]:
        raise HTTPException(status_code=400, detail="Card not found in hand")

    player["hand"].remove(data.card_id)
    player.setdefault("discard", []).append(data.card_id)

    await logger.add_event(
        state, "card_discarded",
        actor=data.player_id,
        payload={"card": data.card_id, "reason": "curse"},
        message=f"{data.player_id} сбрасывает {data.card_id} из-за проклятия."
    )

    await game_service.save_state(game_id, state)
    return {"status": "ok", "discarded": data.card_id}


@router.get("/{game_id}/log")
async def get_game_log(game_id: str):
    state = await game_service.load_state(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Game not found")
    return state.get("log", [])

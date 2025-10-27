# api/ws_payloads.py
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional, Literal
from api.ws_events import WSEvent

# ======== Базовая модель WS-сообщения ========

class WSMessage(BaseModel):
    """Базовая структура WebSocket-сообщения."""
    event: WSEvent
    payload: Optional[Dict[str, Any]] = None


# ======== Состояние игры ========

class StateUpdatePayload(BaseModel):
    """Полное состояние игры для синхронизации клиента."""
    state: Dict[str, Any]


class ActionPerformedPayload(BaseModel):
    """Действие, совершённое игроком."""
    player_id: str
    action_type: str
    result: Optional[Dict[str, Any]] = None


class GameStartedPayload(BaseModel):
    """Событие начала новой игры."""
    state: Dict[str, Any]


class TurnEndedPayload(BaseModel):
    """Окончание хода."""
    state: Dict[str, Any]


# ======== Эффекты и бои ========

class MovePayload(BaseModel):
    actor_id: str
    from_hall: Optional[str] = None
    to_hall: str


class AttackPayload(BaseModel):
    attacker: str
    target: str
    damage: int
    target_hp: int


class TreasureEffectPayload(BaseModel):
    hall: str
    effect: str
    details: Optional[Dict[str, Any]] = None


# ======== Взаимодействие с игроками ========

class ChooseDiscardPayload(BaseModel):
    player_id: str
    hand: List[str]


class CardDiscardedPayload(BaseModel):
    player_id: str
    card_id: str


# ======== Конец игры ========

class GameOverPayload(BaseModel):
    result: Literal["victory", "defeat"]
    reason: Optional[str] = None


# ======== Универсальные модели для логов/ошибок ========

class InfoPayload(BaseModel):
    message: str


class ErrorPayload(BaseModel):
    error: str
    details: Optional[Any] = None


# ======== Утилита для быстрой сборки WS-сообщений ========

def make_ws_message(event: WSEvent, payload: BaseModel | dict | None = None) -> dict:
    """
    Универсальный помощник: возвращает dict для отправки через ws_manager.
    Пример:
        await ws_manager.broadcast(game_id, make_ws_message(WSEvent.STATE_UPDATE, StateUpdatePayload(state=...)))
    """
    if isinstance(payload, BaseModel):
        payload = payload.model_dump()
    return {"event": event, "payload": payload or {}}

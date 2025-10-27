# schemas/player_action.py (добавляем новые типы внизу)

from pydantic import BaseModel, Field
from typing import Literal, Optional, List, Union, Dict, Any

# --- Базовый класс действия ---
class PlayerActionBase(BaseModel):
    game_id: str = Field(..., description="ID текущей партии")
    player_id: str = Field(..., description="ID игрока, совершающего действие")
    action_type: str = Field(..., description="Тип действия игрока")


# --- Существующие действия (без изменений) ---
class PlayCardAction(PlayerActionBase):
    action_type: Literal["play_card"] = "play_card"
    card_id: str
    target_hall: Optional[str] = None


class MoveMonsterAction(PlayerActionBase):
    action_type: Literal["move_monster"] = "move_monster"
    monster_id: str
    from_hall: str
    to_hall: str


class AttackAction(PlayerActionBase):
    action_type: Literal["attack"] = "attack"
    attacker_id: str
    target_hero_id: str
    hall_id: str


class DefendAction(PlayerActionBase):
    action_type: Literal["defend"] = "defend"
    defender_id: str
    card_id: str
    hall_id: str


class BuyCardAction(PlayerActionBase):
    action_type: Literal["buy_card"] = "buy_card"
    hall_id: str
    card_id: str
    resource_type: str


class DiscardCardAction(PlayerActionBase):
    action_type: Literal["discard_card"] = "discard_card"
    card_id: str


# --- Новые схемы для будущих реакций ---
class ReactionAction(PlayerActionBase):
    action_type: Literal["reaction"] = "reaction"
    reaction_type: Literal["defense", "interrupt", "boost"]
    source_card_id: Optional[str] = None
    target_hero_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


# --- Объединённая схема ---
PlayerAction = Union[
    PlayCardAction,
    MoveMonsterAction,
    AttackAction,
    DefendAction,
    BuyCardAction,
    DiscardCardAction,
    ReactionAction,  # ← добавляем без ломки
]

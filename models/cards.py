# models/cards.py
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal


# --- Базовое описание действия на карте ---
class CardAction(BaseModel):
    kind: str  # тип действия ("move", "attack", "summon", "draw_card" и т.д.)
    params: Optional[Dict[str, Any]] = None  # параметры действия


# --- Базовый класс карты ---
class BaseCard(BaseModel):
    id: str
    card_type: str
    actions: List[CardAction] = Field(default_factory=list)


# --- Карта монстра (начальная колода игрока) ---
class MonsterCard(BaseCard):
    card_type: Literal["monster"] = "monster"
    hp: int = 1  # запас здоровья монстра, если карта имеет значение HP


# --- Карта героя (из колоды гильдии) ---
class HeroCard(BaseCard):
    card_type: Literal["hero"] = "hero"
    heroes: List[Dict[str, str]] = Field(default_factory=list)
    # пример: [{"type": "warrior", "hall_tag": "eye"}, {"type": "mage", "hall_tag": "book"}]


# --- Карта магазина (добыча, “loot”) ---
class LootCard(BaseCard):
    card_type: Literal["loot"] = "loot"
    cost: Optional[Dict[str, int]] = None  # {"coin": 1}, {"book": 1}, ...


# --- Карта сценария ---
class ScenarioCard(BaseCard):
    card_type: Literal["scenario"] = "scenario"
    description: Optional[str] = None  # текст сценария (лора)
    special_rules: Optional[List[str]] = None  # особые условия, если есть


# --- Экспорт ---
__all__ = [
    "CardAction",
    "BaseCard",
    "MonsterCard",
    "HeroCard",
    "LootCard",
    "ScenarioCard",
]

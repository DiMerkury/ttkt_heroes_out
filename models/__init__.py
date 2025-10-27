# models/__init__.py
"""
Пакет моделей игры.
Содержит:
 - основные классы состояния (GameState, Hall, Hero, Monster)
 - модели карт и токенов
 - перечисления (enums)
 - схемы действий (PlayerAction и пр.)
"""

# --- Базовые перечисления ---
from .enums import (
    PhaseType,
    DifficultyType,
    CardType,
    LootType,
    HeroType,
    TokenType,
    ActionType,
    ReactionType,
    TreasureEffect,
    GameResult,
)

# --- Основные игровые модели ---
from .game_state import GameState
from .entities import Hall, Hero, Monster, Treasure, Token, Player

# --- Модели карт ---
from .cards import BaseCard, MonsterCard, LootCard, HeroCard, ScenarioCard

# --- Схемы действий (Pydantic) ---
from schemas.player_action import (
    PlayerAction,
    PlayCardAction,
    MoveMonsterAction,
    AttackAction,
    DefendAction,
    BuyCardAction,
    DiscardCardAction,
)

# --- Экспортируем всё необходимое ---
__all__ = [
    # Enums
    "PhaseType",
    "DifficultyType",
    "CardType",
    "LootType",
    "HeroType",
    "TokenType",
    "ActionType",
    "ReactionType",
    "TreasureEffect",
    "GameResult",

    # Models
    "GameState",
    "Hall",
    "Hero",
    "Monster",
    "Treasure",
    "Token",

    # Cards
    "BaseCard",
    "MonsterCard",
    "LootCard",
    "HeroCard",
    "ScenarioCard",

    # Actions
    "PlayerAction",
    "PlayCardAction",
    "MoveMonsterAction",
    "AttackAction",
    "DefendAction",
    "BuyCardAction",
    "DiscardCardAction",
]

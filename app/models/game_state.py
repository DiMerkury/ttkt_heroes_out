from typing import List, Dict, Optional
from .base import TTKTBaseModel, PhaseType
from .player import Player
from .hall import Hall
from .hero import Hero
from .monster import Monster
from .treasure import Treasure

class GameState(TTKTBaseModel):
    id: str
    players: List[Player]
    halls: List[Hall]
    heroes: List[Hero] = []
    monsters: List[Monster] = []
    treasures: List[Treasure] = []
    difficulty: str = "family"
    phase: PhaseType = PhaseType.PLAYER
    wave: int = 0
    game_over: bool = False
    result: Optional[str] = None

    guild_deck: Optional[List[str]] = None
    monster_decks: Optional[Dict[str, List[str]]] = None
    shop_deck: Optional[List[str]] = None

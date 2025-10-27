# models/game_state.py
from __future__ import annotations
import json
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from models.entities import Hall, Hero, Monster, Treasure, Player


class GameState(BaseModel):
    id: str
    phase: str = "setup"
    difficulty: str = "family"

    halls: Dict[str, Hall] = Field(default_factory=dict)
    heroes: List[Hero] = Field(default_factory=list)
    monsters: List[Monster] = Field(default_factory=list)
    treasures: List[Treasure] = Field(default_factory=list)
    players: List[Player] = Field(default_factory=list)

    # --- Новые поля ---
    guild_deck: List[str] = Field(default_factory=list)
    monster_decks: Dict[str, List[dict]] = Field(default_factory=dict)  # {class: [card_json...]}
    shop_deck: List[str] = Field(default_factory=list)

    game_over: bool = False
    result: Optional[str] = None

    def to_dict(self) -> dict:
        return json.loads(self.model_dump_json())

    def to_json(self) -> str:
        return self.model_dump_json(indent=2)

    # --- Методы-хелперы ---
    def assign_player(self, player_id: str, monster_class: str):
        """Назначить игроку конкретный класс монстров."""
        player = Player(id=player_id, name=f"Player {player_id}")
        player.resources = {}
        player.monster_class = monster_class
        self.players.append(player)

    def get_player_deck(self, player_id: str) -> Optional[List[dict]]:
        """Возвращает колоду монстров по ID игрока."""
        player = next((p for p in self.players if p.id == player_id), None)
        if not player:
            return None
        return self.monster_decks.get(player.monster_class, [])

    def get_available_classes(self) -> List[str]:
        """Список классов монстров, доступных для выбора игроками."""
        return list(self.monster_decks.keys())

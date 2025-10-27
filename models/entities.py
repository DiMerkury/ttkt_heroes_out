# models.py
from __future__ import annotations
import json
import random
from enum import Enum
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


# ============================================================
# ENUMS
# ============================================================

class PhaseType(str, Enum):
    PLAYER = "player"
    HEROES = "heroes"
    GAME_OVER = "game_over"


class TreasureEffect(str, Enum):
    ROBBERY = "robbery"     # Сбросить ресурс в зале
    CURSE = "curse"         # Все игроки сбрасывают по карте
    HEAL = "heal"           # Активировать всех героев в зале
    PRISONER = "prisoner"   # Отправить героя в темницу
    DEFEAT = "defeat"       # Поражение игроков


# ============================================================
# CORE ENTITIES
# ============================================================

# --- Жетон (ресурс, ловушка, сокровище) ---
class Token(BaseModel):
    id: str
    token_type: str  # "coin", "frog", "book", "trap", "treasure_1", ...
    value: Optional[int] = None  # для сокровищ (1–4)

class Monster(BaseModel):
    id: str
    name: str
    hp: int = 1
    hall: str
    owner_id: str
    defense_card: Optional[str] = None  # для реакций


class Hero(BaseModel):
    id: str
    name: str
    hp: int = 1
    hall: str
    exhausted: bool = False


class Treasure(BaseModel):
    id: str
    required: int  # сколько героев нужно для кражи
    effect: Optional[TreasureEffect] = None


class Hall(BaseModel):
    id: str
    tokens: List[str] = Field(default_factory=list)
    heroes: List[Hero] = Field(default_factory=list)
    monsters: List[Monster] = Field(default_factory=list)
    treasure: Optional[Treasure] = None

    def get_treasure(self) -> Optional[Treasure]:
        return self.treasure

    def remove_treasure(self):
        self.treasure = None


class Player(BaseModel):
    id: str
    name: str
    hand: List[str] = Field(default_factory=list)
    resources: Dict[str, int] = Field(default_factory=dict)
    defeated: bool = False


# ============================================================
# GAME STATE
# ============================================================

class GameState(BaseModel):
    id: str
    players: List[Player]
    halls: List[Hall]
    heroes: List[Hero]
    monsters: List[Monster]
    guild_deck: List[str]  # колода героев
    difficulty: str = "family"  # "family" | "problem" | "hard"
    phase: PhaseType = PhaseType.PLAYER
    wave: int = 1
    game_over: bool = False
    result: Optional[str] = None

    # -----------------------
    # Utility serialization
    # -----------------------
    def to_dict(self) -> dict:
        return self.model_dump()

    def to_json(self) -> str:
        return json.dumps(self.model_dump(), ensure_ascii=False)

    @classmethod
    def from_json(cls, data: str) -> "GameState":
        return cls(**json.loads(data))

    # -----------------------
    # Helpers for game logic
    # -----------------------
    def get_hall(self, hall_id: str) -> Optional[Hall]:
        return next((h for h in self.halls if h.id == hall_id), None)

    def get_active_heroes(self) -> List[Hero]:
        return [h for h in self.heroes if not h.exhausted and h.hp > 0]

    def get_exhausted_heroes_in_hall(self, hall_id: str) -> List[Hero]:
        return [h for h in self.heroes if h.hall == hall_id and h.exhausted]

    def get_active_heroes_in_hall(self, hall_id: str) -> List[Hero]:
        return [h for h in self.heroes if h.hall == hall_id and not h.exhausted]

    def get_monsters_in_hall(self, hall_id: str) -> List[Monster]:
        return [m for m in self.monsters if m.hall == hall_id]

    def remove_monster(self, monster: Monster):
        if monster in self.monsters:
            self.monsters.remove(monster)
            hall = self.get_hall(monster.hall)
            if hall:
                hall.monsters = [m for m in hall.monsters if m.id != monster.id]

    def remove_hero(self, hero: Hero):
        if hero in self.heroes:
            self.heroes.remove(hero)
            hall = self.get_hall(hero.hall)
            if hall:
                hall.heroes = [h for h in hall.heroes if h.id != hero.id]

    # -----------------------
    # HERO & TREASURE LOGIC
    # -----------------------
    def spawn_heroes_from_deck(self) -> List[Hero]:
        """
        Создаёт героев из верхних карт колоды в зависимости от сложности и волны.
        """
        cards_to_draw = 1
        if self.difficulty == "family":
            cards_to_draw = 1 if self.wave == 1 else 2
        elif self.difficulty == "problem":
            cards_to_draw = 2
        elif self.difficulty == "hard":
            cards_to_draw = 2 if self.wave == 1 else 3

        if not self.guild_deck:
            self.reshuffle_guild_deck()

        drawn_cards = [self.guild_deck.pop(0) for _ in range(min(cards_to_draw, len(self.guild_deck)))]
        new_heroes = []

        for card_id in drawn_cards:
            hall_id = f"hall_{random.randint(1, len(self.halls))}"
            hero = Hero(id=card_id, name=f"Hero {card_id}", hall=hall_id)
            self.heroes.append(hero)
            hall = self.get_hall(hall_id)
            if hall:
                hall.heroes.append(hero)
            new_heroes.append(hero)

        return new_heroes

    def reshuffle_guild_deck(self):
        """
        Перетасовать сброс героев в новую колоду (если потребуется).
        """
        all_ids = [f"H{i}" for i in range(1, 9)]
        random.shuffle(all_ids)
        self.guild_deck = all_ids

    def find_path_toward_treasure(self, current_hall_id: str) -> Optional[str]:
        """
        Простая заглушка для поиска пути: выбирает случайный смежный зал.
        """
        hall_ids = [h.id for h in self.halls if h.id != current_hall_id]
        return random.choice(hall_ids) if hall_ids else None

    def apply_treasure_effect(self, treasure: Treasure) -> TreasureEffect:
        """
        Применяет эффект сокровища (рандомно, по таблице вероятностей).
        """
        effect_table = {
            1: ["robbery", "curse"],
            2: ["curse", "heal"],
            3: ["heal", "prisoner"],
            4: ["defeat"],  # главное сокровище
        }

        candidates = effect_table.get(treasure.required, ["robbery"])
        effect = random.choice(candidates)
        treasure.effect = TreasureEffect(effect)

        if effect == "defeat":
            self.game_over = True
            self.result = "defeat"

        return treasure.effect

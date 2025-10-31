import json
from pathlib import Path
from typing import Any, Dict, List
from app.common.logger import logger

class DataLoader:
    def __init__(self, base_path: str = None):
        # base_path default: package data folder
        base = Path(__file__).parent.parent / "data"
        self.base_path = Path(base_path) if base_path else base
        self.halls: List[Dict[str, Any]] = []
        self.heroes: List[Dict[str, Any]] = []
        self.monster_classes: List[Dict[str, Any]] = []
        self.monster_decks: List[Dict[str, Any]] = []
        self.shop_cards: List[Dict[str, Any]] = []
        self.difficulty_config: Dict[str, Any] = {}
        self.treasure_effects: Dict[str, Any] = {}
        self.scenario: Dict[str, Any] = {}

    def _load_json(self, rel: str):
        p = self.base_path / rel
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.debug(f"[DataLoader] loaded {rel}")
        return data

    def load_all(self):
        self.halls = self._load_json("halls.json")
        self.heroes = self._load_json("heroes.json")
        self.monster_classes = self._load_json("monsters/classes.json")
        self.monster_decks = self._load_json("monsters/decks.json")
        self.shop_cards = self._load_json("shop_cards.json")
        self.difficulty_config = self._load_json("config/difficulty.json")
        self.treasure_effects = self._load_json("config/treasure_effects.json")

    def load_scenario(self, scenario_id: str):
        self.scenario = self._load_json(f"scenario/{scenario_id}.json")
        return self.scenario

    def get_hall(self, hall_id: str):
        for h in self.halls:
            if h["id"] == hall_id:
                return h
        return None

    def get_difficulty(self, level: str):
        return self.difficulty_config.get(level)

    def get_treasure_effects(self, tier: str):
        return self.treasure_effects.get(str(tier), [])

    def validate_all(self):
        # simple validations
        ids = {h["id"] for h in self.halls}
        for h in self.halls:
            for c in h.get("connections", []):
                if c not in ids:
                    logger.warning(f"[DataLoader] Unknown connection: {h['id']} -> {c}")
                else:
                    other = next(x for x in self.halls if x["id"] == c)
                    if h["id"] not in other.get("connections", []):
                        logger.warning(f"[DataLoader] Connection not bidirectional: {h['id']} <-> {c}")

        # check scenario treasury if loaded
        if self.scenario:
            halls = self.scenario.get("halls", [])
            has_treasury = any(x["id"] == "treasury" for x in halls)
            has_token = any("treasury_4" in x.get("tokens", []) for x in halls)
            if not (has_treasury or has_token):
                raise ValueError("Scenario must include 'treasury' hall or 'treasury_4' token.")

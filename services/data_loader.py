# services/data_loader.py
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Union
from pydantic import BaseModel, ValidationError
from common.logger import logger

BASE_PATH = Path(__file__).resolve().parent.parent / "data"


class DataLoader:
    """
    Универсальный загрузчик игровых данных из JSON.
    Проверяет структуру и подготавливает данные для GameService.
    """

    def __init__(self, base_path: Union[str, Path] = BASE_PATH):
        self.base_path = Path(base_path)
        if not self.base_path.exists():
            raise FileNotFoundError(f"Data path not found: {self.base_path}")

    # =====================================================
    # --- Универсальный метод чтения JSON ---
    # =====================================================
    def _load_json(self, relative_path: str) -> Any:
        path = self.base_path / relative_path
        if not path.exists():
            raise FileNotFoundError(f"JSON file not found: {path}")

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            logger.debug(f"[DataLoader] Loaded {relative_path}")
            return data
        except json.JSONDecodeError as e:
            logger.error(f"[DataLoader] JSON decode error in {relative_path}: {e}")
            raise

    # =====================================================
    # --- Загрузка отдельных категорий данных ---
    # =====================================================

    def load_scenario(self, filename: str = "scenario_1.json") -> Dict[str, Any]:
        """
        Загружает сценарий (описание подземелья и соединений между залами).
        """
        data = self._load_json(filename)

        # Проверка базовой структуры
        if "halls" not in data:
            raise ValueError(f"Scenario {filename} missing 'halls' key")

        # Проверяем, что connections и tokens определены
        for hall in data["halls"]:
            hall.setdefault("connections", [])
            hall.setdefault("tokens", [])

        logger.debug(f"[DataLoader] Scenario '{filename}' loaded with {len(data['halls'])} halls.")
        return data

    def load_halls(self) -> List[Dict[str, Any]]:
        """
        Загружает справочник залов (halls.json).
        """
        data = self._load_json("halls.json")
        if not isinstance(data, list):
            raise ValueError("halls.json must be a list of hall definitions")

        # Проверка обязательных ключей
        for hall in data:
            for key in ("id", "label", "spawn", "action", "connections"):
                if key not in hall:
                    raise ValueError(f"Hall missing required key '{key}': {hall}")

        logger.debug(f"[DataLoader] Loaded {len(data)} halls.")
        return data

    def load_heroes(self) -> List[Dict[str, Any]]:
        """
        Загружает героев (heroes.json).
        """
        data = self._load_json("heroes.json")
        if not isinstance(data, list):
            raise ValueError("heroes.json must be a list")

        for hero in data:
            for key in ("id", "name", "hp", "spawn", "behavior"):
                if key not in hero:
                    raise ValueError(f"Hero missing key '{key}': {hero}")

        logger.debug(f"[DataLoader] Loaded {len(data)} heroes.")
        return data

    def load_monster_classes(self) -> Dict[str, Dict[str, Any]]:
        """
        Загружает классы монстров (monsters/classes.json)
        и возвращает их в виде словаря {class_name: data}.
        """
        data = self._load_json("monsters/classes.json")
        if not isinstance(data, list):
            raise ValueError("monsters/classes.json must be a list")

        classes = {entry["class"]: entry for entry in data}
        logger.debug(f"[DataLoader] Loaded {len(classes)} monster classes.")
        return classes

    def load_monster_decks(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Загружает колоды монстров (monsters/decks.json)
        и группирует их по 'class'.
        """
        data = self._load_json("monsters/decks.json")
        if not isinstance(data, list):
            raise ValueError("monsters/decks.json must be a list")

        decks: Dict[str, List[Dict[str, Any]]] = {}
        for card in data:
            cls = card.get("class")
            if not cls:
                raise ValueError(f"Monster card missing class: {card}")
            decks.setdefault(cls, []).append(card)

        logger.debug(f"[DataLoader] Loaded decks for {len(decks)} monster classes.")
        return decks

    def load_shop_cards(self) -> List[Dict[str, Any]]:
        """
        Загружает карты магазина (shop.json).
        """
        data = self._load_json("shop.json")
        if not isinstance(data, list):
            raise ValueError("shop.json must be a list")

        for card in data:
            for key in ("id", "type", "class", "actions"):
                if key not in card:
                    raise ValueError(f"Shop card missing key '{key}': {card}")

        logger.debug(f"[DataLoader] Loaded {len(data)} shop cards.")
        return data

    # =====================================================
    # --- Проверка взаимосвязей ---
    # =====================================================

    def validate_references(self, scenario: Dict[str, Any], halls: List[Dict[str, Any]]):
        """
        Проверяет, что все ссылки (connections, tokens, hall.id) корректны.
        """
        hall_ids = {h["id"] for h in halls}
        for hall in scenario["halls"]:
            # Проверка connections
            for target in hall["connections"]:
                if target not in hall_ids:
                    raise ValueError(f"Invalid hall connection: {hall['id']} -> {target}")

            # Проверка токенов
            for token in hall.get("tokens", []):
                if not isinstance(token, str):
                    raise ValueError(f"Invalid token format in hall {hall['id']}: {token}")

        logger.debug("[DataLoader] Scenario references validated successfully.")

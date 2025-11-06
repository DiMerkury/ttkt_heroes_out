import json
import random
from pathlib import Path
from typing import Any, Dict, List
from app.common.logger import logger


class DataLoader:
    """
    Загрузчик данных для игры 'Героям тут не место'.

    Отвечает за:
    - загрузку справочников (залы, герои, монстры, карты магазина);
    - загрузку сценариев;
    - базовую валидацию данных;
    - дополнительную проверку целостности (check_data_integrity).
    """

    def __init__(self, base_path: str = None):
        base = Path(__file__).parent.parent / "data"
        self.base_path = Path(base_path) if base_path else base

        # Основные справочники
        self.halls: List[Dict[str, Any]] = []
        self.heroes: List[Dict[str, Any]] = []
        self.monster_classes: List[Dict[str, Any]] = []
        self.monster_decks: List[Dict[str, Any]] = []
        self.shop_cards: List[Dict[str, Any]] = []

        # Конфигурации
        self.difficulty_config: Dict[str, Any] = {}
        self.treasure_effects: Dict[str, Any] = {}

        # Активный сценарий
        self.scenario: Dict[str, Any] = {}

    # ----------------------------
    # Базовая загрузка
    # ----------------------------
    def _load_json(self, rel: str):
        p = self.base_path / rel
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.debug(f"[DataLoader] loaded {rel}")
        return data

    def load_all(self):
        """Загрузка всех базовых данных."""
        self.halls = self._load_json("halls.json")
        self.heroes = self._load_json("heroes.json")
        self.monster_classes = self._load_json("monsters/classes.json")
        self.monster_decks = self._load_json("monsters/decks.json")
        self.shop_cards = self._load_json("shop_cards.json")
        self.difficulty_config = self._load_json("config/difficulty.json")
        self.treasure_effects = self._load_json("config/treasure_effects.json")

    def load_scenario(self, scenario_id: str):
        """Загружает один сценарий."""
        path = self.base_path / f"scenario/{scenario_id}.json"
        if not path.exists():
            raise FileNotFoundError(f"Scenario '{scenario_id}' not found in {path}")
        self.scenario = self._load_json(f"scenario/{scenario_id}.json")
        logger.info(f"[DataLoader] Loaded scenario '{scenario_id}'")
        return self.scenario

    # ----------------------------
    # Утилиты доступа
    # ----------------------------
    def get_hall(self, hall_id: str):
        return next((h for h in self.halls if h["id"] == hall_id), None)

    def get_difficulty(self, level: str):
        return self.difficulty_config.get(level)

    def get_treasure_effects(self, tier: str):
        return self.treasure_effects.get(str(tier), [])
    
    def get_treasure_effects_for_id(self, treasure_id: str):
        """
        Возвращает список эффектов для указанного treasure_id вида 'treasury_2'.
        Если структура treasure_effects хранится по ключу-уровню ('1','2',...),
        то извлекаем номер из id и возвращаем соответствующий список.
        """
        if not treasure_id:
            return []
        # ожидаем формат вида 'treasury_2' или 'treasury-2' — берем цифры
        s = "".join(ch for ch in treasure_id if ch.isdigit())
        if not s:
            return []
        return self.treasure_effects.get(s, [])

    def collect_treasures_from_scenario(self, scenario: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Для каждого зала сценария, где указано 'treasure',
        создаёт уникальное сокровище с рандомными эффектами.
        """
        if not scenario:
            return []

        treasures_list: List[Dict[str, Any]] = []
        for h in scenario.get("halls", []):
            base_tid = h.get("treasure")
            if not base_tid:
                continue

            # создаём уникальный id, чтобы сокровища не пересекались
            tid = f"{base_tid}_{h.get('id')}"

            # извлекаем цифру уровня, например 'treasury_3' → 3
            digits = "".join(ch for ch in str(base_tid) if ch.isdigit())
            tier = int(digits) if digits.isdigit() else 1

            # случайный выбор эффектов
            effects_all = self.get_treasure_effects(tier) or self.get_treasure_effects_for_id(base_tid)
            if not effects_all:
                effects_all = ["none"]

            # num_effects = random.randint(1, min(3, len(effects_all)))
            # effects = random.sample(effects_all, k=num_effects)
            effects = random.sample(effects_all, k=min(1, len(effects_all)))
            logger.debug(f"[Treasure] base_tid={base_tid} effects_all={effects_all}")
            logger.debug(f"[Treasure] chosen effects={effects}")

            treasures_list.append({
                "id": tid,
                "tier": tier,
                "effects": effects,
                "opened": False,
                "location": h.get("id"),
            })

        return treasures_list  

    # ----------------------------
    # Валидация
    # ----------------------------
    def validate_all(self):
        """Базовая валидация сценария и залов."""
        if not self.halls:
            raise ValueError("Halls data not loaded before validation.")

        if self.scenario:
            halls_dict = {h["id"]: h for h in self.halls}

            # Проверка залов сценария против справочника
            for sh in self.scenario.get("halls", []):
                hid = sh["id"]
                base = halls_dict.get(hid)
                if not base:
                    logger.warning(f"[DataLoader] Unknown hall id '{hid}' in scenario.")
                    continue

                max_conn = base.get("max_connections")
                if max_conn is not None and len(sh.get("connections", [])) > max_conn:
                    logger.warning(
                        f"[DataLoader] '{hid}' has {len(sh['connections'])} connections (max {max_conn})."
                    )

            # Проверка двусторонних связей
            ids = {h["id"] for h in self.scenario.get("halls", [])}
            for h in self.scenario.get("halls", []):
                for c in h.get("connections", []):
                    if c not in ids:
                        logger.warning(f"[DataLoader] Unknown connection: {h['id']} -> {c}")
                    else:
                        other = next(x for x in self.scenario["halls"] if x["id"] == c)
                        if h["id"] not in other.get("connections", []):
                            logger.warning(
                                f"[DataLoader] Connection not bidirectional: {h['id']} <-> {c}"
                            )

            # Проверка наличия сокровищницы
            has_treasury = any(x["id"] == "treasury" for x in self.scenario["halls"])
            has_token = any(
                "treasury_4" in x.get("tokens", []) for x in self.scenario["halls"]
            )
            if not (has_treasury or has_token):
                raise ValueError(
                    "Scenario must include 'treasury' hall or 'treasury_4' token."
                )

    # ----------------------------
    # Проверка целостности данных
    # ----------------------------
    def check_data_integrity(self, scenario_id: str | None = None, full_check: bool = False):
        """
        Проверяет целостность данных.
        full_check=True — полная проверка (для CLI);
        full_check=False — быстрая проверка (для GameInitializer).
        """
        logger.info("[DataLoader] Checking data integrity...")

        if full_check:
            # ------------------------------------------------
            # Проверяем halls.json
            # ------------------------------------------------
            hall_ids = set()
            for hall in self.halls:
                hid = hall.get("id")
                if not hid:
                    logger.error("[Integrity] Hall missing 'id'.")
                    continue
                if hid in hall_ids:
                    logger.warning(f"[Integrity] Duplicate hall id: {hid}")
                hall_ids.add(hid)

                for field in ["label", "spawn", "action", "max_connections"]:
                    if field not in hall:
                        logger.debug(f"[Integrity] Hall '{hid}' missing optional field '{field}'.")

            # ------------------------------------------------
            # Если указан сценарий — собираем активные spawn-теги
            # ------------------------------------------------
            scenario_spawn_tags = set()
            if scenario_id:
                try:
                    scenario = self._load_json(f"scenario/{scenario_id}.json")
                    active_hall_ids = {h.get("id") for h in scenario.get("halls", []) if h.get("id")}
                    scenario_spawn_tags = {
                        hall.get("spawn")
                        for hall in self.halls
                        if hall.get("id") in active_hall_ids and hall.get("spawn")
                    }
                    logger.debug(
                        f"[Integrity] Collected spawn tags from halls.json for scenario '{scenario_id}': "
                        f"{scenario_spawn_tags}"
                    )
                except FileNotFoundError:
                    logger.error(f"[Integrity] Scenario '{scenario_id}' not found.")

            # ------------------------------------------------
            # Проверяем героев
            # ------------------------------------------------
            for hero in self.heroes:
                hid = hero.get("id")
                if not hid:
                    logger.error("[Integrity] Hero missing 'id'.")
                    continue

                if not hero.get("name") or not hero.get("hp"):
                    logger.error(f"[Integrity] Hero '{hid}' missing required fields (name/hp).")

                spawn = hero.get("spawn")
                if scenario_id and spawn and spawn not in scenario_spawn_tags:
                    logger.warning(
                        f"[Integrity] Hero '{hid}' has spawn='{spawn}' "
                        f"but no hall with such spawn tag in scenario '{scenario_id}'."
                    )

                if not hero.get("behavior"):
                    logger.debug(f"[Integrity] Hero '{hid}' has no 'behavior' declared.")

            # ------------------------------------------------
            # Проверяем классы монстров
            # ------------------------------------------------
            mc_ids = {m["class"] for m in self.monster_classes if "class" in m}
            if len(mc_ids) != len(self.monster_classes):
                logger.warning("[Integrity] Duplicate monster class IDs detected.")

            # ------------------------------------------------
            # Проверяем колоды монстров
            # ------------------------------------------------
            for deck in self.monster_decks:
                cls = deck.get("class")
                if cls and cls not in mc_ids:
                    logger.warning(f"[Integrity] Deck refers to unknown monster class: {cls}")

            # ------------------------------------------------
            # Проверяем карты магазина
            # ------------------------------------------------
            card_ids = set()
            for card in self.shop_cards:
                cid = card.get("id")
                if not cid:
                    logger.error("[Integrity] Shop card missing 'id'.")
                    continue
                if cid in card_ids:
                    logger.warning(f"[Integrity] Duplicate shop card id: {cid}")
                card_ids.add(cid)

            # ------------------------------------------------
            # Проверяем конфиги
            # ------------------------------------------------
            if not self.difficulty_config:
                logger.warning("[Integrity] difficulty.json is empty or missing.")
            if not self.treasure_effects:
                logger.warning("[Integrity] treasure_effects.json is empty or missing.")

            logger.info("[DataLoader] Data integrity check completed successfully.")

        else:
            hall_ids = {h.get("id") for h in self.halls if h.get("id")}
            if not hall_ids:
                logger.error("[Integrity] No halls loaded.")
                return

            # ------------------------------------------------
            # Если указан сценарий — собираем spawn-теги залов, присутствующих в сценарии
            # ------------------------------------------------
            scenario_spawn_tags = set()
            if scenario_id:
                path = self.base_path / f"scenario/{scenario_id}.json"
                if not path.exists():
                    logger.error(f"[Integrity] Scenario '{scenario_id}' not found.")
                else:
                    scenario = self._load_json(f"scenario/{scenario_id}.json")
                    active_halls = {h.get("id") for h in scenario.get("halls", [])}
                    scenario_spawn_tags = {
                        h["spawn"] for h in self.halls if h["id"] in active_halls and h.get("spawn")
                    }
                    logger.debug(
                        f"[Integrity] Scenario '{scenario_id}' active spawn tags: {scenario_spawn_tags}"
                    )

            # Проверка героев на корректные spawn
            for hero in self.heroes:
                spawn = hero.get("spawn")
                if scenario_id and spawn and spawn not in scenario_spawn_tags:
                    logger.warning(
                        f"[Integrity] Hero '{hero['id']}' spawn='{spawn}' not in scenario '{scenario_id}'."
                    )

            logger.info("[DataLoader] Data integrity check completed successfully.")


# ------------------------------------------------
# CLI-запуск для ручной проверки
# ------------------------------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="DataLoader integrity check")
    parser.add_argument(
        "--check",
        metavar="SCENARIO_ID",
        nargs="?",
        const="default",
        help="Проверить целостность данных (опционально указать сценарий, например 'intro' или 'campaign_1').",
    )
    args = parser.parse_args()

    loader = DataLoader()
    loader.load_all()

    if args.check is not None:
        scenario = None if args.check == "default" else args.check
        loader.check_data_integrity(scenario_id=scenario, full_check=True)
        print(f"\n[CLI] Integrity check finished for scenario: {scenario or 'ALL'}")
    else:
        print("Для проверки целостности используйте: python -m app.services.data_loader --check [scenario_id]")

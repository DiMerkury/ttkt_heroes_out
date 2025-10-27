# services/game_service.py
import json
from typing import Optional, List
from common.logger import logger
from models import GameState, PhaseType
from services.hero_ai_service import HeroAIService
from services.rule_engine import RuleEngine
from services.game_log_service import GameLogService
from services.data_loader import DataLoader


class GameService:
    """
    Основной сервис управления состоянием игры.
    Работает с Redis и управляет фазами, волнами и логикой.
    """

    def __init__(self, redis):
        self.redis = redis
        self.hero_ai = HeroAIService(redis)
        self.log_service = GameLogService(redis)
        self.rule_engine = RuleEngine()
        self.rule_engine.bind_log_service(self.log_service)
        self.data_loader = DataLoader()

    # =====================================================
    # --- Работа с состоянием ---
    # =====================================================

    async def load_state(self, game_id: str) -> Optional[GameState]:
        """
        Загружает состояние из Redis.
        """
        key = f"game:{game_id}"
        data = await self.redis.get(key)
        if not data:
            logger.warning(f"[GAME_SERVICE] Game {game_id} not found in Redis")
            return None

        try:
            state = GameState.from_json(data)
            logger.debug(f"[GAME_SERVICE] Loaded game {game_id}")
            return state
        except Exception as e:
            logger.error(f"[GAME_SERVICE] Failed to decode game state: {e}")
            return None

    async def save_state(self, game_id: str, state: GameState):
        """
        Сохраняет текущее состояние в Redis.
        """
        key = f"game:{game_id}"
        await self.redis.set(key, state.to_json())
        logger.debug(f"[GAME_SERVICE] Saved game {game_id}")

    async def update_state(self, game_id: str):
        """
        Принудительно обновляет состояние (например, после реакций).
        """
        state = await self.load_state(game_id)
        if not state:
            return None
        await self.save_state(game_id, state)
        return state

    # =====================================================
    # --- Инициализация новой партии ---
    # =====================================================

    async def create_game(
        self,
        game_id: str,
        player_names: List[str],
        difficulty: str = "family",
    ) -> GameState:
        """
        Создаёт новую игру, используя данные из data/.
        """
        logger.info(f"[GAME_SERVICE] Creating new game {game_id} ({difficulty})")

        # Загружаем базовые данные
        scenario = self.data_loader.load_scenario("scenario_1.json")
        heroes = self.data_loader.load_heroes()
        monster_classes = self.data_loader.load_monster_classes()
        monster_decks = self.data_loader.load_monster_decks()
        shop_cards = self.data_loader.load_shop_cards()

        # Проверка, что сценарий содержит сокровищницу
        treasury_present = any(
            "treasury_4" in hall.get("tokens", [])
            or hall.get("id") == "treasury"
            for hall in scenario["halls"]
        )
        if not treasury_present:
            raise ValueError("Scenario must contain a treasury hall or treasure_4 token")

        # Формируем игроков
        players = []
        for i, name in enumerate(player_names):
            monster_class = list(monster_classes.keys())[i % len(monster_classes)]
            players.append({
                "id": f"p{i+1}",
                "name": name,
                "monster_class": monster_class,
                "hand": [],
                "resources": {},
            })

        # Создаём состояние
        state = GameState(
            id=game_id,
            phase=PhaseType.PLAYER,
            difficulty=difficulty,
            halls={h["id"]: h for h in scenario["halls"]},
            heroes=[],
            monsters=[],
            treasures=[],
            game_over=False,
            result=None,
        )

        await self.save_state(game_id, state)
        logger.info(f"[GAME_SERVICE] Game {game_id} initialized successfully.")
        return state

    # =====================================================
    # --- Управление волнами и фазами ---
    # =====================================================

    async def start_next_wave(self, state: GameState):
        """
        Переход к следующей волне героев.
        """
        if state.game_over:
            logger.warning(f"[GAME_SERVICE] Game {state.id} already over.")
            return state

        state.phase = PhaseType.HEROES
        state.wave += 1
        await self.save_state(state.id, state)
        logger.info(f"[GAME_SERVICE] Starting wave {state.wave} in game {state.id}")

        hero_log = await self.hero_ai.run_wave(state)
        logger.debug(f"[GAME_SERVICE] Hero wave complete: {len(hero_log)} events")

        if state.game_over:
            logger.warning(f"[GAME_SERVICE] Game over in wave {state.wave}")
            await self.save_state(state.id, state)
            return state

        state.phase = PhaseType.PLAYER
        await self.save_state(state.id, state)
        return state

    async def check_victory(self, state: GameState) -> bool:
        """
        Проверка победы игроков (например, все волны завершены).
        """
        if state.wave > 2 and not state.game_over:
            state.phase = PhaseType.GAME_OVER
            state.game_over = True
            state.result = "victory"
            await self.save_state(state.id, state)
            logger.info(f"[GAME_SERVICE] Game {state.id} victory!")
            return True
        return False

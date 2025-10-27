# services/game_service.py
import json
from typing import Optional
from common.logger import logger
from models import GameState, Hall, Player, Monster, Hero, Treasure, PhaseType
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

        state = GameState.from_json(data)
        logger.debug(f"[GAME_SERVICE] Loaded game {game_id}")
        return state

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
        player_names: list[str],
        scenario_id: str,
        difficulty: str = "family",
    ) -> GameState:
        """
        Создаёт новую партию на основе данных из JSON.
        Загружает сценарий, героев, классы монстров и колоды.
        """
        logger.info(f"[GAME_SERVICE] Creating new game {game_id} ({scenario_id})")

        # --- Загрузка данных ---
        scenario = self.data_loader.load_scenario(scenario_id)
        heroes = self.data_loader.load_heroes()
        monster_classes = self.data_loader.load_monster_classes()
        monster_decks = self.data_loader.load_monster_decks()
        halls = self.data_loader.load_halls()

        # --- Инициализация игроков ---
        players = [
            Player(
                id=f"p{i+1}",
                name=name,
                resources={"gold": 0, "souls": 0},
            )
            for i, name in enumerate(player_names)
        ]

        # --- Подготовка залов из сценария ---
        scenario_halls = []
        for hall_data in scenario["halls"]:
            base = next((h for h in halls if h["id"] == hall_data["id"]), None)
            if not base:
                logger.warning(f"[GAME_SERVICE] Hall {hall_data['id']} not found in base data")
                continue

            hall = Hall(
                id=base["id"],
                tokens=hall_data.get("tokens", []),
                heroes=[],
                monsters=[],
                treasure=None,
            )
            scenario_halls.append(hall)

        # --- Проверка наличия сокровищницы ---
        has_treasure_hall = any(h.id == "treasury" for h in scenario_halls)
        has_treasure_token = any("treasury_4" in h.tokens for h in scenario_halls)
        if not (has_treasure_hall or has_treasure_token):
            raise ValueError("Сценарий должен содержать зал 'treasury' или токен 'treasury_4'.")

        # --- Формирование стартового состояния ---
        state = GameState(
            id=game_id,
            players=players,
            halls=scenario_halls,
            heroes=[],
            monsters=[],
            treasures=[],
            difficulty=difficulty,
            phase=PhaseType.PLAYER,
            game_over=False,
        )

        # --- Лог ---
        await self.log_service.add_entry(
            game_id,
            entry_type="game_start",
            payload={
                "players": [p.name for p in players],
                "scenario": scenario_id,
                "difficulty": difficulty,
            },
        )

        # --- Сохраняем ---
        await self.save_state(game_id, state)
        logger.info(f"[GAME_SERVICE] Game {game_id} initialized.")
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
        Проверка победы игроков.
        """
        if state.wave > 2 and not state.game_over:
            state.phase = PhaseType.GAME_OVER
            state.game_over = True
            state.result = "victory"
            await self.save_state(state.id, state)
            logger.info(f"[GAME_SERVICE] Game {state.id} victory!")
            return True
        return False

# services/phase_manager.py
import asyncio
from common.logger import logger
from models import PhaseType
from services.game_service import GameService


class PhaseManager:
    """
    Управляет переходами между фазами игры:
    - PLAYER → HEROES (нашествие героев)
    - HEROES → PLAYER (новый ход)
    - Завершение игры (victory / defeat)
    """

    def __init__(self, redis):
        self.redis = redis
        self.game_service = GameService(redis)

    async def next_phase(self, game_id: str):
        """
        Переход к следующей фазе.
        """
        state = await self.game_service.load_state(game_id)
        if not state:
            logger.warning(f"[PHASE_MANAGER] Game {game_id} not found")
            return None

        logger.info(f"[PHASE_MANAGER] Current phase: {state.phase}")

        if state.game_over:
            logger.info(f"[PHASE_MANAGER] Game {game_id} already finished.")
            return state

        if state.phase == PhaseType.PLAYER:
            # Завершение хода игрока → начинается волна героев
            await self.start_hero_phase(state)
        elif state.phase == PhaseType.HEROES:
            # Герои завершили действия → новый ход игроков
            await self.start_player_phase(state)
        elif state.phase == PhaseType.GAME_OVER:
            logger.info(f"[PHASE_MANAGER] Game {game_id} already over.")
        else:
            logger.warning(f"[PHASE_MANAGER] Unknown phase: {state.phase}")

        return state

    # =====================================================
    # --- Основные переходы ---
    # =====================================================

    async def start_player_phase(self, state):
        """
        Переход к фазе игроков.
        """
        state.phase = PhaseType.PLAYER
        state.turn += 1
        await self.game_service.save_state(state.id, state)
        logger.info(f"[PHASE_MANAGER] Player phase started (turn {state.turn})")

    async def start_hero_phase(self, state):
        """
        Переход к фазе героев — разыгрываются карты гильдии.
        """
        state.phase = PhaseType.HEROES
        await self.game_service.save_state(state.id, state)
        logger.info(f"[PHASE_MANAGER] Hero phase started (wave {state.wave})")

        # Запускаем ИИ героев
        await self._run_hero_wave(state)

    # =====================================================
    # --- Вспомогательные методы ---
    # =====================================================

    async def _run_hero_wave(self, state):
        """
        Запуск волны героев с учётом уровня сложности.
        """
        difficulty = state.difficulty or "family"
        cards_to_play = self._get_hero_cards_count(difficulty, state.wave)
        logger.info(f"[PHASE_MANAGER] Hero wave: playing {cards_to_play} guild cards")

        for _ in range(cards_to_play):
            if not state.guild_deck:
                # если колода гильдии закончилась
                if not state.wave_reshuffled:
                    state.wave_reshuffled = True
                    state.wave = 2
                    state.guild_deck = state.discarded_guild.copy()
                    state.shuffle_guild_deck()
                    logger.info(f"[PHASE_MANAGER] Guild deck reshuffled (wave 2)")
                else:
                    # Победа игроков
                    state.game_over = True
                    state.result = "victory"
                    await self.game_service.save_state(state.id, state)
                    logger.info(f"[PHASE_MANAGER] Game {state.id} victory!")
                    return

            # Разыгрываем карту героев
            await self.game_service.hero_ai.run_wave(state)

            if state.game_over:
                logger.warning(f"[PHASE_MANAGER] Game {state.id} over (defeat detected)")
                await self.game_service.save_state(state.id, state)
                return

        # После завершения волны — проверяем победу
        if await self.game_service.check_victory(state):
            return

        # Возвращаемся в фазу игроков
        await self.start_player_phase(state)

    def _get_hero_cards_count(self, difficulty: str, wave: int) -> int:
        """
        Возвращает количество карт гильдии, которое нужно разыграть
        в зависимости от уровня сложности и текущей волны.
        """
        mapping = {
            "family": {1: 1, 2: 2},
            "problem": {1: 2, 2: 2},
            "hard": {1: 2, 2: 3},
        }
        return mapping.get(difficulty, mapping["family"]).get(wave, 1)

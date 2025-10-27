# services/action_service.py
from common.logger import logger
from models import PlayerAction
from services.rule_engine import RuleEngine
from services.game_service import GameService
from services.phase_manager import PhaseManager
from services.game_log_service import GameLogService

# WebSocket utils
from api.ws_manager import ws_manager
from api.ws_events import WSEvent
from api.ws_payloads import (
    ActionPerformedPayload,
    StateUpdatePayload,
    ChooseDiscardPayload,
    CardDiscardedPayload,
    make_ws_message,
)

# Дополнительно — если есть реакции
from schemas.player_action import ReactionAction


class ActionService:
    """Сервис обработки действий игроков с фазами и логами."""

    def __init__(self, redis):
        self.redis = redis
        self.game_service = GameService(redis)
        self.log_service = GameLogService(redis)

        # Создаём RuleEngine и связываем с логами
        self.rule_engine = RuleEngine()
        self.rule_engine.bind_log_service(self.log_service)

        self.phase_manager = PhaseManager(redis)

    async def process_action(self, action: PlayerAction):
        """Обработка действий игрока."""
        logger.info(f"[ACTION] {action.action_type} by {action.player_id}")

        # Загружаем состояние игры
        game_state = await self.game_service.load_state(action.game_id)
        if not game_state:
            logger.warning(f"Game {action.game_id} not found")
            return {"error": "Game not found"}

        # Применяем действие
        result = await self.rule_engine.apply_action(game_state, action)
        await self.game_service.save_state(action.game_id, game_state)

        # --- WS: оповещение о действии ---
        await ws_manager.broadcast(
            action.game_id,
            make_ws_message(
                WSEvent.ACTION_PERFORMED,
                ActionPerformedPayload(
                    player_id=action.player_id,
                    action_type=action.action_type,
                    result=result,
                ),
            ),
        )

        # --- WS: обновление состояния ---
        await ws_manager.broadcast(
            action.game_id,
            make_ws_message(WSEvent.STATE_UPDATE, StateUpdatePayload(state=game_state.to_dict())),
        )

        # --- Проверка фазы ---
        await self.phase_manager.next_phase(action.game_id)

        logger.debug(f"[ACTION] done {action.action_type}")
        return {"ok": True, "result": result}

    async def request_discard(self, game_id: str, player_id: str, hand: list[str]):
        """Эффект 'Проклятие': запросить сброс карты."""
        await ws_manager.send_to_player(
            game_id,
            player_id,
            make_ws_message(
                WSEvent.CHOOSE_DISCARD,
                ChooseDiscardPayload(player_id=player_id, hand=hand),
            ),
        )
        logger.info(f"[DISCARD_REQUEST] sent to {player_id}")

    async def notify_discarded(self, game_id: str, player_id: str, card_id: str):
        """Уведомление о сброшенной карте."""
        await ws_manager.broadcast(
            game_id,
            make_ws_message(
                WSEvent.CARD_DISCARDED,
                CardDiscardedPayload(player_id=player_id, card_id=card_id),
            ),
        )
        logger.debug(f"[CARD_DISCARDED] {player_id} -> {card_id}")

    async def process_reaction(self, action: ReactionAction):
        """Реакции (defense / interrupt / boost) — пока базовая заглушка."""
        logger.info(f"[REACTION] {action.reaction_type} from {action.player_id}")

        await ws_manager.broadcast(
            action.game_id,
            make_ws_message(
                WSEvent.ACTION_PERFORMED,
                ActionPerformedPayload(
                    player_id=action.player_id,
                    action_type=f"reaction:{action.reaction_type}",
                    result={"ok": True},
                ),
            ),
        )
        logger.debug(f"[REACTION_DONE] {action.reaction_type} from {action.player_id}")
        return {"ok": True}

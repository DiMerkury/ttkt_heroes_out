# services/rule_engine.py
from common.logger import logger
from models import GameState, PlayerAction
from models.entities import Hall, Monster, Hero
from models.enums import PhaseType
from services.game_log_service import GameLogService


class RuleEngine:
    """Главный обработчик игровых действий (логика правил)."""

    def __init__(self):
        self.log_service: GameLogService | None = None

    def bind_log_service(self, log_service: GameLogService):
        """Позволяет подключить логгер действий (для централизованной записи событий)."""
        self.log_service = log_service

    async def apply_action(self, state: GameState, action: PlayerAction) -> dict:
        """Основная точка входа: применяет действие к состоянию."""
        handler_name = f"_handle_{action.action_type}"
        handler = getattr(self, handler_name, None)

        if not handler:
            logger.warning(f"[RULE_ENGINE] No handler for action '{action.action_type}'")
            return {"error": f"Unknown action '{action.action_type}'"}

        logger.debug(f"[RULE_ENGINE] Executing {action.action_type} by {action.player_id}")
        result = await handler(state, action)

        if self.log_service:
            await self.log_service.write(state.id, f"Action: {action.action_type}", data=result)

        return result

    # =============================================================
    # HANDLERS
    # =============================================================

    async def _handle_play_card(self, state: GameState, action):
        """Игрок разыгрывает карту (призыв монстра или действие)."""
        player = next((p for p in state.players if p.id == action.player_id), None)
        if not player:
            return {"error": "Player not found"}

        if action.card_id not in player.hand:
            return {"error": "Card not in hand"}

        # Удаляем карту из руки
        player.hand.remove(action.card_id)

        # Добавляем логическое действие (упрощённо — призыв монстра)
        hall = state.get_hall(action.target_hall or "hall_1")
        monster = Monster(
            id=f"monster_{len(state.monsters)+1}",
            name="Summoned Monster",
            hp=1,
            hall=hall.id,
            owner_id=player.id,
        )
        state.monsters.append(monster)
        hall.monsters.append(monster)

        msg = f"{player.name} разыгрывает карту {action.card_id} и призывает монстра в {hall.id}"
        logger.info(f"[RULE_ENGINE] {msg}")

        return {"ok": True, "event": "summon", "monster_id": monster.id}

    async def _handle_move_monster(self, state: GameState, action):
        """Перемещение монстра из одного зала в другой."""
        monster = next((m for m in state.monsters if m.id == action.monster_id), None)
        if not monster:
            return {"error": "Monster not found"}

        hall_from = state.get_hall(action.from_hall)
        hall_to = state.get_hall(action.to_hall)

        if not hall_from or not hall_to:
            return {"error": "Invalid hall"}

        hall_from.monsters = [m for m in hall_from.monsters if m.id != monster.id]
        hall_to.monsters.append(monster)
        monster.hall = hall_to.id

        msg = f"{monster.name} перемещается из {hall_from.id} в {hall_to.id}"
        logger.debug(f"[RULE_ENGINE] {msg}")

        return {"ok": True, "event": "move", "from": hall_from.id, "to": hall_to.id}

    async def _handle_attack(self, state: GameState, action):
        """Монстр атакует героя в том же зале."""
        monster = next((m for m in state.monsters if m.id == action.attacker_id), None)
        hero = next((h for h in state.heroes if h.id == action.target_hero_id), None)
        if not monster or not hero:
            return {"error": "Invalid attacker or target"}

        if hero.hall != monster.hall:
            return {"error": "Target not in same hall"}

        hero.hp -= 1
        msg = f"{monster.name} атакует {hero.name} (-1 HP)"
        logger.debug(f"[RULE_ENGINE] {msg}")

        if hero.hp <= 0:
            state.remove_hero(hero)
            msg += f" — {hero.name} погибает!"
        if self.log_service:
            await self.log_service.write(state.id, msg)

        return {"ok": True, "event": "attack", "target_hp": hero.hp}

    async def _handle_buy_card(self, state: GameState, action):
        """Покупка карты из магазина."""
        player = next((p for p in state.players if p.id == action.player_id), None)
        hall = state.get_hall(action.hall_id)
        if not player or not hall:
            return {"error": "Invalid player or hall"}

        # Проверяем наличие ресурса
        if action.resource_type not in hall.tokens:
            return {"error": "No required resource in hall"}

        hall.tokens.remove(action.resource_type)
        player.hand.append(action.card_id)

        msg = f"{player.name} покупает карту {action.card_id} за {action.resource_type} в {hall.id}"
        logger.info(f"[RULE_ENGINE] {msg}")
        return {"ok": True, "event": "buy_card", "card_id": action.card_id}

    async def _handle_discard_card(self, state: GameState, action):
        """Игрок сбрасывает карту (например, при Проклятии)."""
        player = next((p for p in state.players if p.id == action.player_id), None)
        if not player:
            return {"error": "Player not found"}

        if action.card_id not in player.hand:
            return {"error": "Card not in hand"}

        player.hand.remove(action.card_id)
        msg = f"{player.name} сбрасывает карту {action.card_id}"
        logger.debug(f"[RULE_ENGINE] {msg}")
        if self.log_service:
            await self.log_service.write(state.id, msg)
        return {"ok": True, "event": "discard", "card_id": action.card_id}

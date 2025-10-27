# services/hero_ai_service.py
import random
from common.logger import logger
from api.ws_manager import ws_manager
from api.ws_events import WSEvent
from api.ws_payloads import (
    MovePayload,
    AttackPayload,
    TreasureEffectPayload,
    StateUpdatePayload,
    make_ws_message,
)
from services.game_log_service import GameLogService


class HeroAIService:
    """
    ИИ героев: выполняет фазы героев по шагам правил (1–8).
    """

    def __init__(self, redis):
        self.redis = redis
        self.log_service = GameLogService(redis)

    async def run_wave(self, state):
        """
        Запуск волны героев (весь цикл 1–8 по правилам).
        Возвращает лог действий героев.
        """
        logger.info(f"[HERO_AI] Running hero wave...")
        hero_log = []

        # === 1. Призыв героев (из колоды гильдии) ===
        new_heroes = state.spawn_heroes_from_deck()
        for hero in new_heroes:
            entry = f"Призван герой {hero.name} в зал {hero.hall}"
            hero_log.append(entry)
            await self.log_service.log_hero_action(state.id, hero.name, "spawn", hero.hall)

        logger.debug(f"[HERO_AI] Spawned heroes: {len(new_heroes)}")

        # === 2–8. Для каждого активного героя выполняем цикл ===
        active_heroes = state.get_active_heroes()
        for hero in active_heroes:
            entry = await self.run_hero_turn(state, hero)
            hero_log.extend(entry)

        # === Обновляем состояние ===
        await self.save_and_broadcast_state(state)

        logger.info(f"[HERO_AI] Wave complete ({len(hero_log)} events)")
        await self.log_service.log_wave(state.id, state.wave, len(hero_log))
        return hero_log

    async def run_hero_turn(self, state, hero):
        """
        Полный цикл хода одного героя (этапы 3–8).
        """
        log = []
        hall = state.get_hall(hero.hall)
        if not hall:
            return log

        # === 3. Проверка ловушек ===
        traps = [t for t in hall.tokens if t == "trap"]
        for _ in traps:
            hero.hp -= 1
            hall.tokens.remove("trap")
            msg = f"{hero.name} попал в ловушку (-1 HP)"
            log.append(msg)
            await self.log_service.log_hero_action(state.id, hero.name, "trap", hall.id)

            if hero.hp <= 0:
                state.remove_hero(hero)
                log.append(f"{hero.name} погиб")
                await self.log_service.log_hero_action(state.id, hero.name, "death", hall.id)
                return log

        # === 4. Воодушевление ===
        allies = state.get_exhausted_heroes_in_hall(hall.id)
        if allies:
            for ally in allies:
                ally.exhausted = False
            msg = f"{hero.name} воодушевил {len(allies)} героев"
            log.append(msg)
            await self.log_service.log_hero_action(state.id, hero.name, "inspire", hall.id)

        # === 5. Атака (если есть монстр) ===
        monsters = state.get_monsters_in_hall(hall.id)
        if monsters:
            target = random.choice(monsters)
            target.hp -= 1
            msg = f"{hero.name} атакует {target.name} (-1 HP)"
            log.append(msg)
            await self.log_service.log_hero_action(state.id, hero.name, "attack", hall.id)

            await ws_manager.broadcast(
                state.id,
                make_ws_message(
                    WSEvent.ATTACK,
                    AttackPayload(
                        attacker=hero.name,
                        target=target.name,
                        damage=1,
                        target_hp=target.hp,
                    ),
                ),
            )

            if target.hp <= 0:
                state.remove_monster(target)
                msg = f"Монстр {target.name} побеждён!"
                log.append(msg)
                await self.log_service.log_hero_action(state.id, target.name, "defeated", hall.id)

            hero.exhausted = True
            return log

        # === 6. Кража сокровища ===
        treasure = hall.get_treasure()
        if treasure:
            active_heroes = state.get_active_heroes_in_hall(hall.id)
            if len(active_heroes) >= treasure.required:
                hall.remove_treasure()
                effect = state.apply_treasure_effect(treasure)
                msg = f"Герои крадут сокровище {treasure.id} ({effect})"
                log.append(msg)

                await self.log_service.log_treasure_effect(state.id, effect, hall.id)

                await ws_manager.broadcast(
                    state.id,
                    make_ws_message(
                        WSEvent.TREASURE_EFFECT,
                        TreasureEffectPayload(hall=hall.id, effect=effect),
                    ),
                )

                if effect == "defeat":
                    state.game_over = True
                    state.result = "defeat"
                    await self.log_service.log_game_over(state.id, "treasure_4_stolen")
                    log.append("Герои похитили главное сокровище! Поражение!")
                return log
            else:
                hero.exhausted = True
                msg = f"{hero.name} ждёт подкрепления у сокровища"
                log.append(msg)
                await self.log_service.log_hero_action(state.id, hero.name, "wait", hall.id)
                return log

        # === 8. Рывок (движение) ===
        next_hall_id = state.find_path_toward_treasure(hall.id)
        if next_hall_id:
            hero.hall = next_hall_id
            msg = f"{hero.name} перемещается в зал {next_hall_id}"
            log.append(msg)
            await self.log_service.log_hero_action(state.id, hero.name, "move", next_hall_id)

            await ws_manager.broadcast(
                state.id,
                make_ws_message(
                    WSEvent.MOVE,
                    MovePayload(actor_id=hero.name, from_hall=hall.id, to_hall=next_hall_id),
                ),
            )

            # Рекурсивно — герой может снова действовать
            log.extend(await self.run_hero_turn(state, hero))

        return log

    async def save_and_broadcast_state(self, state):
        """
        Сохранить состояние и оповестить клиентов.
        """
        await self.redis.set(f"game:{state.id}", state.to_json())
        await ws_manager.broadcast(
            state.id,
            make_ws_message(WSEvent.STATE_UPDATE, StateUpdatePayload(state=state.to_dict())),
        )

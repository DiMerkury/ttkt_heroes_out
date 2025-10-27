# services/game_log_service.py
import json
import datetime
from common.logger import logger


class GameLogService:
    """
    Сервис ведения журнала действий и событий игры.
    Использует Redis-список как хранилище логов.
    """

    def __init__(self, redis):
        self.redis = redis

    def _key(self, game_id: str) -> str:
        return f"game:{game_id}:log"

    async def add_entry(self, game_id: str, entry_type: str, payload: dict):
        """
        Добавить новую запись в лог.
        """
        log_entry = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "type": entry_type,
            "payload": payload,
        }
        key = self._key(game_id)
        await self.redis.rpush(key, json.dumps(log_entry))
        logger.debug(f"[LOG] + {entry_type} -> {payload}")

    async def get_log(self, game_id: str, limit: int = 100):
        """
        Получить последние N записей из лога.
        """
        key = self._key(game_id)
        entries = await self.redis.lrange(key, -limit, -1)
        return [json.loads(e) for e in entries]

    async def clear_log(self, game_id: str):
        """
        Очистить лог (например, при старте новой партии).
        """
        await self.redis.delete(self._key(game_id))

    # --- Специализированные события ---
    async def log_hero_action(self, game_id: str, hero_id: str, action: str, hall_id: str):
        await self.add_entry(
            game_id,
            "hero_action",
            {"hero_id": hero_id, "action": action, "hall_id": hall_id},
        )

    async def log_treasure_effect(self, game_id: str, effect_type: str, hall_id: str):
        await self.add_entry(
            game_id,
            "treasure_effect",
            {"effect_type": effect_type, "hall_id": hall_id},
        )

    async def log_wave(self, game_id: str, wave_num: int, cards_played: int):
        await self.add_entry(
            game_id,
            "wave_start",
            {"wave": wave_num, "cards_played": cards_played},
        )

    async def log_game_over(self, game_id: str, reason: str):
        await self.add_entry(game_id, "game_over", {"reason": reason})

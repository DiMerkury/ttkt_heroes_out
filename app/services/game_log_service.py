import json
from datetime import datetime
from app.common.logger import logger

class GameLogService:
    def __init__(self, redis):
        self.redis = redis

    async def add_entry(self, game_id: str, entry_type: str, payload):
        entry = {"timestamp": datetime.utcnow().isoformat(), "type": entry_type, "payload": payload}
        key = f"game:{game_id}:log"
        await self.redis.client.rpush(key, json.dumps(entry, ensure_ascii=False))
        logger.debug(f"[GameLog] {game_id} <- {entry_type}")

    async def get_log(self, game_id: str):
        key = f"game:{game_id}:log"
        raw = await self.redis.client.lrange(key, 0, -1)
        return [json.loads(x) for x in raw]

    async def clear_log(self, game_id: str):
        key = f"game:{game_id}:log"
        await self.redis.delete(key)

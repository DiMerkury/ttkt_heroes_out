import json
import redis.asyncio as aioredis
from typing import Optional
from app.common.config import REDIS_URL
from app.common.logger import logger

class RedisStorage:
    def __init__(self, url: Optional[str] = None):
        url = url or REDIS_URL
        self.client = aioredis.from_url(url, decode_responses=True)

    async def get(self, key: str):
        v = await self.client.get(key)
        if v is None:
            return None
        try:
            return json.loads(v)
        except Exception:
            logger.exception("Failed to parse JSON from Redis for key %s", key)
            return None

    async def set(self, key: str, value, ex: int = None):
        await self.client.set(key, json.dumps(value, ensure_ascii=False), ex=ex)

    async def delete(self, key: str):
        await self.client.delete(key)

    async def rpush(self, key: str, value: str):
        await self.client.rpush(key, value)

    async def lrange(self, key: str, start: int = 0, end: int = -1):
        return await self.client.lrange(key, start, end)

    async def exists(self, key: str) -> bool:
        return bool(await self.client.exists(key))

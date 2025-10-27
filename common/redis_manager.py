import json
import redis.asyncio as aioredis
from typing import Optional
from common.config import REDIS_URL

class RedisStorage:
    def __init__(self, url: Optional[str]=None):
        url = url or REDIS_URL
        self.client = aioredis.from_url(url, decode_responses=True)

    async def get(self, key: str):
        v = await self.client.get(key)
        if v is None:
            return None
        return json.loads(v)

    async def set(self, key: str, value, ex: int=None):
        await self.client.set(key, json.dumps(value), ex=ex)

    async def delete(self, key: str):
        await self.client.delete(key)

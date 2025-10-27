import json
import asyncio

class RedisStore:
    def __init__(self):
        self._data = {}

    async def set_json(self, key: str, value: dict):
        self._data[key] = json.dumps(value)

    async def get_json(self, key: str):
        data = self._data.get(key)
        return json.loads(data) if data else None

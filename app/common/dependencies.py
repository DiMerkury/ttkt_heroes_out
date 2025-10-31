from app.common.redis_manager import RedisStorage

_redis_instance = RedisStorage()

async def get_redis() -> RedisStorage:
    return _redis_instance

# common/dependencies.py
from common.redis_manager import RedisStorage

# создаём один экземпляр RedisStorage для всего приложения
_storage = RedisStorage()

async def get_redis() -> RedisStorage:
    """Возвращает общий экземпляр RedisStorage (через Depends)"""
    return _storage

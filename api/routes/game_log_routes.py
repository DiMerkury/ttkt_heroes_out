from fastapi import APIRouter, Depends
from services.game_log_service import GameLogService
from common.redis import get_redis

router = APIRouter(prefix="/game", tags=["Game Log"])


@router.get("/{game_id}/log")
async def get_game_log(game_id: str, limit: int = 100, redis=Depends(get_redis)):
    """
    Получить журнал действий игры.
    """
    log_service = GameLogService(redis)
    return await log_service.get_log(game_id, limit=limit)

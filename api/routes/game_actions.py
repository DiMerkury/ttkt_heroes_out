from fastapi import APIRouter, Depends, HTTPException
from schemas.player_action import PlayerAction
from services.action_service import ActionService
from services.game_service import GameService
from services.rule_engine import RuleEngine
from services.hero_ai_service import HeroAIService
from utils.logger import logger

router = APIRouter(prefix="/game", tags=["Game Actions"])

# ⚙️ Зависимости — обычно инициализируются при старте приложения
game_service = GameService()
rule_engine = RuleEngine()
hero_ai = HeroAIService()
action_service = ActionService(game_service, rule_engine, hero_ai)


@router.post("/{game_id}/action")
async def perform_action(game_id: str, action: PlayerAction):
    """
    Принимает действие игрока (разыграть карту, передвинуть монстра, атаковать и т.д.)
    и вызывает соответствующий обработчик.
    """
    try:
        if action.game_id != game_id:
            raise HTTPException(status_code=400, detail="Game ID mismatch")

        logger.info(f"🎮 POST /game/{game_id}/action — получено действие {action.action_type}")
        result = await action_service.handle_action(action)

        return {"status": "ok", "result": result}

    except Exception as e:
        logger.exception(f"Ошибка при обработке действия: {e}")
        raise HTTPException(status_code=500, detail=str(e))

from app.common.logger import logger
from app.models import GameState, PhaseType
from app.services.data_loader import DataLoader
from app.services.game_initializer import GameInitializer
from app.services.hero_ai_service import HeroAIService
from app.services.game_log_service import GameLogService
from app.services.rule_engine import RuleEngine

class GameService:
    def __init__(self, redis):
        self.redis = redis
        self.loader = DataLoader()
        self.initializer = GameInitializer(redis)
        self.hero_ai = HeroAIService(redis)
        self.log_service = GameLogService(redis)
        self.rule_engine = RuleEngine()
        self.rule_engine.bind_log_service(self.log_service)

    async def load_state(self, game_id: str):
        data = await self.redis.get(f"game:{game_id}")
        if not data:
            return None
        return GameState(**data)

    async def save_state(self, game_id: str, state: GameState):
        await self.redis.set(f"game:{game_id}", state.to_dict())

    async def get_state(self, game_id: str):
        s = await self.load_state(game_id)
        return s.to_dict() if s else None

    async def create_game(self, game_id: str, player_names: list[str], scenario_id: str, difficulty: str = "family"):
        state = await self.initializer.create_new_game(game_id, player_names, scenario_id, difficulty)
        await self.log_service.add_entry(game_id, "game_start", {"players":[p.name for p in state.players], "scenario": scenario_id})
        await self.save_state(game_id, state)
        return state

    async def start_next_wave(self, game_id: str):
        state = await self.load_state(game_id)
        if not state:
            return None
        if state.game_over:
            return state
        state.phase = PhaseType.HEROES
        state.wave += 1
        await self.save_state(game_id, state)
        await self.log_service.add_entry(game_id, "wave_start", {"wave": state.wave})
        actions = await self.hero_ai.run_wave(state)
        # after wave, check victory
        await self.check_victory(state)
        if not state.game_over:
            state.phase = PhaseType.PLAYER
            await self.log_service.add_entry(game_id, "phase_change", {"phase":"player"})
        await self.save_state(game_id, state)
        return state

    async def check_victory(self, state: GameState):
        # simple: victory after configured max waves in scenario or 3 by default
        scenario = None
        try:
            scenario = self.loader.load_scenario(state.id if False else state.id)  # placeholder
        except Exception:
            scenario = None
        maxw = 3
        if state.wave >= maxw and not state.game_over:
            state.game_over = True
            state.result = "victory"
            await self.log_service.add_entry(state.id, "game_victory", {"wave": state.wave})
            return True
        return False

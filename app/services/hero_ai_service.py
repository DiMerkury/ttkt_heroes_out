import random
from app.common.logger import logger
from app.models import GameState, Hero, Hall
from app.services.rule_engine import RuleEngine
from app.services.game_log_service import GameLogService

class HeroAIService:
    def __init__(self, redis):
        self.redis = redis
        self.rule_engine = RuleEngine()
        self.log_service = GameLogService(redis)

    async def run_wave(self, state: GameState):
        logger.info(f"[HeroAI] Starting wave {state.wave} for game {state.id}")
        actions = []
        if not state.heroes:
            state.heroes = []
            # spawn simple heroes
            for i in range(1, min(3, state.wave + 1) + 1):
                h = Hero(id=f"h{state.wave}_{i}", name=f"Hero_{state.wave}_{i}", hp=5 + state.wave, attack=2, defense=1, location="prison", status="active")
                state.heroes.append(h)
            await self.log_service.add_entry(state.id, "heroes_spawn", {"count": len(state.heroes)})

        for hero in list(state.heroes):
            # move
            current = next((x for x in state.halls if x.id == hero.location), None)
            if not current:
                # try set to a start hall if exists
                if state.halls:
                    hero.location = state.halls[0].id
                    current = state.halls[0]
            if current and current.connections:
                next_id = random.choice(current.connections)
                from_id = hero.location
                hero.location = next_id
                await self.log_service.add_entry(state.id, "hero_move", {"hero": hero.name, "from": from_id, "to": next_id})
                actions.append({"type":"move","hero":hero.name,"from":from_id,"to":next_id})

            # check tokens
            current_after = next((x for x in state.halls if x.id == hero.location), None)
            if current_after:
                for token in list(current_after.tokens):
                    if token.startswith("treasury_"):
                        tier = token.split("_")[1]
                        await self.rule_engine.apply_treasure_effect(state, tier)
                        await self.log_service.add_entry(state.id, "treasure_open", {"hero": hero.name, "tier": tier})
                        actions.append({"type":"treasure","hero":hero.name,"tier":tier})
        logger.info(f"[HeroAI] Wave {state.wave} finished with {len(actions)} actions")
        return actions

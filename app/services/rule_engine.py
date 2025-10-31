from app.common.logger import logger
from app.models import GameState
from app.services.data_loader import DataLoader

class RuleEngine:
    def __init__(self):
        self.log_service = None

    def bind_log_service(self, log_service):
        self.log_service = log_service

    async def apply_treasure_effect(self, state: GameState, tier: str):
        loader = DataLoader()
        loader.load_all()
        effects = loader.get_treasure_effects(tier) or []
        logger.info(f"[RuleEngine] Applying effects {effects} for tier {tier}")
        for eff in effects:
            if eff == "robbery":
                await self._robbery(state)
            elif eff == "curse":
                await self._curse(state)
            elif eff == "heal":
                await self._heal(state)
            elif eff == "prisoner":
                await self._prisoner(state)
            elif eff == "defeat":
                await self._defeat(state)

    async def _robbery(self, state: GameState):
        for p in state.players:
            if p.resources.get("gold", 0) > 0:
                p.resources["gold"] -= 1
        if self.log_service:
            await self.log_service.add_entry(state.id, "effect_robbery", {})

    async def _curse(self, state: GameState):
        for p in state.players:
            if p.hand:
                discarded = p.hand.pop(0)
                if self.log_service:
                    await self.log_service.add_entry(state.id, "effect_curse", {"player": p.name, "card": discarded})

    async def _heal(self, state: GameState):
        for h in state.heroes:
            h.hp += 2
        if self.log_service:
            await self.log_service.add_entry(state.id, "effect_heal", {})

    async def _prisoner(self, state: GameState):
        # move first hero (if any) to prison or create captive
        if state.heroes:
            hero = state.heroes.pop(0)
            # find prison hall
            prison = next((x for x in state.halls if x.id == "prison"), None)
            if prison:
                prison.tokens.append("prisoner")
        if self.log_service:
            await self.log_service.add_entry(state.id, "effect_prisoner", {})

    async def _defeat(self, state: GameState):
        state.game_over = True
        state.result = "defeat"
        if self.log_service:
            await self.log_service.add_entry(state.id, "effect_defeat", {"result":"defeat"})

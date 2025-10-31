from app.common.logger import logger
from app.models import GameState, Player, Hall, Treasure
from app.services.data_loader import DataLoader

class GameInitializer:
    def __init__(self, redis):
        self.redis = redis
        self.loader = DataLoader()

    async def create_new_game(self, game_id: str, player_names: list[str], scenario_id: str, difficulty: str = "family") -> GameState:
        self.loader.load_all()
        scenario = self.loader.load_scenario(scenario_id)
        self.loader.validate_all()

        # create halls from scenario using base hall defs
        hall_defs = {h["id"]: h for h in self.loader.halls}
        halls = []
        for h in scenario.get("halls", []):
            base = hall_defs.get(h["id"], {})
            hall = Hall(
                id=h["id"],
                label=base.get("label"),
                spawn=base.get("spawn"),
                action=base.get("action"),
                connections=h.get("connections", base.get("connections", [])),
                tokens=h.get("tokens", []),
            )
            halls.append(hall)

        # players
        players = []
        monster_classes = self.loader.monster_classes
        monster_decks = self.loader.monster_decks
        for i, name in enumerate(player_names):
            mc = monster_classes[i]["class"] if i < len(monster_classes) else None
            deck = [c["id"] for c in monster_decks if c["class"] == mc]
            players.append(Player(id=f"p{i+1}", name=name, monster_class=mc, deck=deck))

        # treasures (simple fill)
        treasures = []
        for t in scenario.get("treasures", []):
            tr = Treasure(id=t.get("id"), tier=t.get("tier", 1), effects=self.loader.get_treasure_effects(t.get("tier", 1)), opened=False, location=t.get("location"))
            treasures.append(tr)

        state = GameState(
            id=game_id,
            players=players,
            halls=halls,
            heroes=[],
            monsters=[],
            treasures=treasures,
            difficulty=difficulty,
            phase="player",
            wave=0,
            game_over=False,
        )

        await self.redis.set(f"game:{game_id}", state.to_dict())
        logger.info(f"[GameInitializer] created game {game_id}")
        return state

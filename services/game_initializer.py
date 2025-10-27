import json
from common.logger import logger
from models import GameState, Player, Hall, Token, Treasure
from services.data_loader import DataLoader


class GameInitializer:
    """
    Формирует стартовое состояние партии.
    - Загружает данные через DataLoader
    - Создаёт пустые комнаты, колоды и токены
    - Не расставляет монстров (игроки выбирают сами)
    """

    def __init__(self, redis):
        self.redis = redis
        self.loader = DataLoader()

    async def create_new_game(self, game_id: str, player_names: list[str], difficulty: str = "family") -> GameState:
        """
        Создаёт новое состояние игры для данного списка игроков.
        """
        logger.info(f"[GameInitializer] Creating new game {game_id} ({len(player_names)} players)")

        # --- Загружаем все данные ---
        self.loader.load_all()
        self.loader._validate_connections()
        self.loader._validate_monsters()
        self.loader._validate_scenario_treasury()

        # --- Создаём залы ---
        halls: dict[str, Hall] = {}
        for hall_info in self.loader.scenario["halls"]:
            hall_id = hall_info["id"]
            halls[hall_id] = Hall(
                id=hall_id,
                tokens=hall_info.get("tokens", []),
                heroes=[],
                monsters=[],
                treasure=None
            )

        # --- Колоды героев, магазина и монстров ---
        guild_deck = [h["id"] for h in self.loader.heroes]
        shop_deck = [s["id"] for s in self.loader.shop_cards]

        # Колоды монстров — по одной для каждого класса
        monster_classes = self.loader.monster_classes
        monster_decks = {}
        for deck_card in self.loader.monster_decks:
            cls = deck_card["class"]
            monster_decks.setdefault(cls, []).append(deck_card)

        # --- Формируем игроков ---
        # Каждый игрок выбирает уникальный класс монстра
        players: list[Player] = []
        for i, name in enumerate(player_names):
            if i >= len(monster_classes):
                logger.warning(f"[GameInitializer] Not enough monster classes for player {name}")
                break
            monster_class = monster_classes[i]["class"]
            player = Player(
                id=f"p{i+1}",
                name=name,
                hand=[],
                resources={},
                defeated=False
            )
            player.monster_class = monster_class
            player.deck = [c["id"] for c in monster_decks.get(monster_class, [])]
            players.append(player)

        # --- Итоговое состояние ---
        state = GameState(
            id=game_id,
            difficulty=difficulty,
            halls=halls,
            heroes=[],
            monsters=[],
            treasures=[],
            guild_deck=guild_deck,
            monster_decks=monster_decks,
            shop_deck=shop_deck,
            players=players,
            game_over=False,
            result=None,
        )

        # --- Сохраняем в Redis ---
        await self.redis.set(f"game:{game_id}", state.to_json())
        logger.info(f"[GameInitializer] Game {game_id} initialized with {len(players)} players")
        return state

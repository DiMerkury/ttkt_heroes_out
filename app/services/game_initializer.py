import random
from app.common.logger import logger
from app.models import GameState, Player, Hall, Treasure, ShopCard, ShopDeck
from app.services.data_loader import DataLoader


class GameInitializer:
    """
    Отвечает за создание нового игрового состояния из данных, загружаемых через DataLoader.
    """

    def __init__(self, redis):
        self.redis = redis
        self.loader = DataLoader()

    async def create_new_game(
        self,
        game_id: str,
        player_names: list[str],
        scenario_id: str,
        difficulty: str = "family",
    ) -> GameState:
        # Загружаем все данные и сценарий
        self.loader.load_all()
        scenario = self.loader.load_scenario(scenario_id)

        # Проверяем данные и целостность
        self.loader.validate_all()
        self.loader.check_data_integrity(scenario_id)

        # ---- Залы ----
        hall_defs = {h["id"]: h for h in self.loader.halls}
        halls = []
        for h in scenario.get("halls", []):
            base = hall_defs.get(h["id"], {})
            halls.append(
                Hall(
                    id=h["id"],
                    label=base.get("label"),
                    spawn=base.get("spawn"),
                    action=base.get("action"),
                    connections=h.get("connections", []),
                    tokens=h.get("tokens", []),
                    max_connections=base.get("max_connections"),
                )
            )

        # ---- Игроки ----
        players = []
        # for i, name in enumerate(player_names):
        #     mc = None
        #     if i < len(self.loader.monster_classes):
        #         mc = self.loader.monster_classes[i].get("class")
        #     deck = [c["id"] for c in self.loader.monster_decks if c.get("class") == mc]
        #     players.append(Player(id=f"p{i+1}", name=name, monster_class=mc, deck=deck))
        monster_classes = self.loader.monster_classes
        monster_decks = self.loader.monster_decks

        for i, name in enumerate(player_names):
            mc = monster_classes[i]["class"] if i < len(monster_classes) else None
            deck = [c["id"] for c in monster_decks if c["class"] == mc]

            player = Player(id=f"p{i+1}", name=name, monster_class=mc, deck=deck)
            player.shuffle_deck()         # 🔹 перемешиваем
            player.draw_starting_hand(5)  # 🔹 берём стартовую руку

            players.append(player)        

        # ---- Сокровища ----
        # treasures = [
        #     Treasure(
        #         id=t.get("id"),
        #         tier=t.get("tier", 1),
        #         effects=self.loader.get_treasure_effects(t.get("tier", 1)),
        #         opened=False,
        #         location=t.get("location"),
        #     )
        #     for t in scenario.get("treasures", [])
        # ]
        # Извлекаем список сокровищ из сценария через DataLoader
        treasure_dicts = self.loader.collect_treasures_from_scenario(scenario)
        treasures = [Treasure(**t) for t in treasure_dicts]

        # Привязываем сокровища к соответствующим залам по полю location
        treasure_by_location = {t.location: t for t in treasures if t.location}
        for hall in halls:
            if hall.id in treasure_by_location:
                hall.treasure = treasure_by_location[hall.id]

        # ---- Колода героев ----
        guild_deck = [h["id"] for h in self.loader.heroes]
        random.shuffle(guild_deck)


        # # Создаём объекты Treasure
        # for tid in treasure_ids:
        #     tier_str = tid.replace("treasury_", "")
        #     tier = int(tier_str) if tier_str.isdigit() else 1

        #     treasures.append(
        #         Treasure(
        #             id=tid,
        #             tier=tier,
        #             effects=self.loader.get_treasure_effects(tid),
        #             opened=False,
        #             location=None,  # привяжем позже при сборке залов
        #         )
        #     )        

        # ---- Колода магазина ---
        shop_cards_data = self.loader.shop_cards 
        shop_cards = [ShopCard(**card_data) for card_data in shop_cards_data]
        shop_deck_obj = ShopDeck(cards=shop_cards)
        shop_deck_obj.setup_display()    
        # Теперь shop_deck готов к использованию:
        # shop_deck.display → 5 карт витрины
        # shop_deck.cards → оставшиеся карты в колоде 
        
        # Сериализуем состояния магазина для хранения в GameState
        # shop_deck_ids — оставшиеся id карт в стопке (в порядке, верхняя — конец списка)
        shop_deck_ids = [c.id for c in shop_deck_obj.cards]

        # shop_display_list — полные словари данных (удобно для UI)
        shop_display_list = [c.model_dump() for c in shop_deck_obj.display]
        # Когда игрок покупает карту:

        #     * в рантайме используй ShopDeck объект 
        #       (или реализуй логику в сервисе магазина), чтобы:
        #           * убрать карту из display,

        #           * при необходимости взять карту из cards и пополнить display.

        #     * после изменений обновляй game_state.shop_deck и game_state.shop_display 
        #       так же, как в инициализации (пересоздавая списки из объекта).
        #     
        # Если у тебя нет живого ShopDeck в памяти после инициализации — можно 
        # при каждом действии реконструировать ShopDeck из shop_deck и shop_display. 
        # Но проще хранить рабочий объект в сервисе игры, а в GameState — только 
        # сериализуемое представление.
        # def serialize_shopdeck(shop_deck_obj):
        #     return {
        #         "shop_deck": [c.id for c in shop_deck_obj.cards],
        #         "shop_display": [c.model_dump() for c in shop_deck_obj.display],
        #     }
        # Используй её при инициализации и после операций покупки.

        # ---- Формирование состояния ----
        state = GameState(
            id=game_id,
            players=players,
            halls=halls,
            heroes=[],
            monsters=[],
            treasures=treasures,
            difficulty=difficulty,
            phase="player",
            current_player_id=players[0].id,
            wave=0,
            game_over=False,
            guild_deck=guild_deck,
            shop_deck=shop_deck_ids,
            shop_display=shop_display_list,
        )

        await self.redis.set(f"game:{game_id}", state.to_dict())
        logger.info(f"[GameInitializer] Created game '{game_id}' using scenario '{scenario_id}'")
        return state

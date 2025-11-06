import random
from typing import List, Optional
from pydantic import Field
from .base import TTKTBaseModel


class ShopCard(TTKTBaseModel):
    """
    Карта магазина — аналог карты монстра, но покупается за определённый ресурс.
    """
    id: str
    type: str = "shop_card"
    class_id: str = Field(alias="class")  # 'pet', 'undead', 'demon' и т.п.
    actions: List[List[dict]] = Field(default_factory=list)

    def __str__(self):
        return f"<ShopCard id={self.id}, class={self.class_id}>"

    class Config:
        allow_population_by_field_name = True


class ShopDeck(TTKTBaseModel):
    """
    Колода магазина: отвечает за перемешивание и управление "витриной" из доступных для покупки карт.
    """
    cards: List[ShopCard] = Field(default_factory=list)
    display: List[ShopCard] = Field(default_factory=list)  # 5 карт, доступных для покупки

    DISPLAY_SIZE: int = 5

    def shuffle(self):
        """Перемешать колоду."""
        random.shuffle(self.cards)

    def setup_display(self):
        """Создать стартовую витрину магазина."""
        self.shuffle()
        self.display = [self.cards.pop() for _ in range(min(self.DISPLAY_SIZE, len(self.cards)))]

    def buy_card(self, card_id: str) -> Optional[ShopCard]:
        """
        Покупка карты с витрины — возвращает карту и обновляет витрину.
        """
        for i, card in enumerate(self.display):
            if card.id == card_id:
                bought_card = self.display.pop(i)
                self._refill_display()
                return bought_card
        return None

    def _refill_display(self):
        """Если есть карты в колоде — пополнить витрину до 5 карт."""
        while len(self.display) < self.DISPLAY_SIZE and self.cards:
            self.display.append(self.cards.pop())

    def is_empty(self) -> bool:
        """Проверить, пуста ли колода."""
        return not self.cards and not self.display

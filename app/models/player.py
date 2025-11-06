from typing import List, Optional
from random import shuffle
from pydantic import Field
from .base import TTKTBaseModel


class Player(TTKTBaseModel):
    """
    Игрок управляет несколькими монстрами одного класса и имеет личную колоду карт.
    """

    id: str
    name: str
    monster_class: Optional[str] = None  # Класс монстров, которым управляет игрок

    hand: List[str] = Field(default_factory=list)           # id карт в руке
    deck: List[str] = Field(default_factory=list)           # id карт в колоде
    discard_pile: List[str] = Field(default_factory=list)   # id карт в сбросе
    monsters: List[str] = Field(default_factory=list)       # id монстров под контролем игрока

    defeated: bool = False

    def shuffle_deck(self):
        """Перемешать текущую колоду."""
        shuffle(self.deck)    

    def draw_card(self):
        """
        Взять верхнюю карту из колоды в руку.
        Если колода пуста, возвращает сброс в колоду и перемешивает.
        """
        if not self.deck and self.discard_pile:
            # Возвращаем сброс в колоду и перемешиваем
            self.deck = self.discard_pile.copy()
            self.discard_pile.clear()
            self.shuffle_deck()

        if self.deck:
            card = self.deck.pop()
            self.hand.append(card)
            return card
        else:
            return None  # колода пуста
        
    def draw_starting_hand(self, count: int = 5):
        """Взять стартовую руку."""
        for _ in range(min(count, len(self.deck))):
            self.draw_card()
            
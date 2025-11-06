from typing import List, Dict
from .base import TTKTBaseModel


class MonsterCard(TTKTBaseModel):
    """
    Карта действий монстров конкретного класса.
    Загружается из data/monsters/decks.json
    """

    id: str
    type: str
    class_id: str
    actions: List[List[Dict[str, str]]]
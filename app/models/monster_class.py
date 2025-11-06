from .base import TTKTBaseModel


class MonsterClass(TTKTBaseModel):
    """
    Архетип монстра, определяет базовые параметры класса.
    Загружается из data/monsters/classes.json
    """

    id: str
    description: str
    hp: int
    cards: int
    max_count: int
    kind: str
    spawn_count: int
    spawn: str
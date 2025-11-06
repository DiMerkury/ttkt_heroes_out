from typing import Optional
from pydantic import Field
from .base import TTKTBaseModel


class Monster(TTKTBaseModel):
    """
    Конкретный монстр на поле. Принадлежит игроку.
    """

    id: str
    class_id: str
    owner_id: str
    hp: int

    location: Optional[str] = None
    resources: Optional[str] = None
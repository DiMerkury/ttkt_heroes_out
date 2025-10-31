from typing import Optional
from .base import TTKTBaseModel

class Monster(TTKTBaseModel):
    id: str
    name: str
    hp: int
    attack: int
    defense: int
    class_id: str
    location: Optional[str] = None
    owner_id: Optional[str] = None

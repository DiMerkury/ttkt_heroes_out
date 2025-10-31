from typing import Optional
from .base import TTKTBaseModel

class Hero(TTKTBaseModel):
    id: str
    name: str
    hp: int
    attack: int
    defense: int
    location: Optional[str] = None
    status: Optional[str] = None

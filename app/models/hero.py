from typing import Optional
from .base import TTKTBaseModel

class Hero(TTKTBaseModel):
    id: str
    name: str
    hp: int = 1
    spawn: Optional[str] = None          # тег зала, где спавнится герой (eye, hat, bones, swords)
    behavior: Optional[str] = None       # идентификатор поведения
    location: Optional[str] = None
    status: Optional[str] = None

from typing import List, Dict, Optional
from pydantic import Field
from .base import TTKTBaseModel

class Player(TTKTBaseModel):
    id: str
    name: str
    monster_class: Optional[str] = None
    hand: List[str] = Field(default_factory=list)
    deck: List[str] = Field(default_factory=list)
    discard_pile: List[str] = Field(default_factory=list)
    resources: Dict[str, int] = Field(default_factory=lambda: {"gold": 0, "souls": 0})
    defeated: bool = False

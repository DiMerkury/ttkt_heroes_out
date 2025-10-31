from typing import List, Optional
from pydantic import Field
from .base import TTKTBaseModel

class Treasure(TTKTBaseModel):
    id: str
    tier: int
    effects: List[str] = Field(default_factory=list)
    opened: bool = False
    location: Optional[str] = None

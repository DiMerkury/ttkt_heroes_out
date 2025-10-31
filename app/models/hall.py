from typing import List, Optional
from pydantic import Field
from .base import TTKTBaseModel

class Hall(TTKTBaseModel):
    id: str
    label: Optional[str] = None
    spawn: Optional[str] = None
    action: Optional[str] = None
    connections: List[str] = Field(default_factory=list)
    tokens: List[str] = Field(default_factory=list)
    heroes: List[str] = Field(default_factory=list)
    monsters: List[str] = Field(default_factory=list)
    treasure: Optional[str] = None

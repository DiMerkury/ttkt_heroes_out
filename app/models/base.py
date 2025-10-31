from enum import Enum
from pydantic import BaseModel

class PhaseType(str, Enum):
    PLAYER = "player"
    HEROES = "heroes"
    GAME_OVER = "game_over"

class TTKTBaseModel(BaseModel):
    def to_json(self) -> str:
        return self.model_dump_json(indent=2, ensure_ascii=False)
    @classmethod
    def from_json(cls, data: str):
        return cls.model_validate_json(data)
    def to_dict(self):
        return self.model_dump()

from pydantic import BaseModel
from typing import List, Dict, Any

class GameCreateRequest(BaseModel):
    difficulty: str = "normal"

class GameStateResponse(BaseModel):
    id: str
    turn: int
    wave: int
    difficulty: str
    players: List[Dict[str, Any]]
    halls: List[Dict[str, Any]]
    heroes: List[Dict[str, Any]]
    log: List[str]
    event_history: List[Dict[str, Any]] = []

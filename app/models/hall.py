from typing import List, Optional
from pydantic import Field
import logging
from .base import TTKTBaseModel
from .treasure import Treasure

logger = logging.getLogger(__name__)

class Hall(TTKTBaseModel):
    id: str
    label: Optional[str] = None
    spawn: Optional[str] = None
    action: Optional[str] = None

    # connections — только для сценариев
    connections: Optional[List[str]] = Field(default_factory=list)

    # tokens — только для сценариев
    tokens: Optional[List[str]] = Field(default_factory=list)

    # служебное поле для справочника залов
    max_connections: Optional[int] = None

    # runtime-поля
    heroes: List[str] = Field(default_factory=list)
    monsters: List[str] = Field(default_factory=list)
    treasure: Optional[Treasure] = None
    open_portal: bool = False

    def open_portal_if_closed(self) -> bool:
        """
        Проверяет наличие закрытого портала в токенах.
        Если найден — удаляет 'closed_portal' и устанавливает open_portal = True.
        Возвращает True, если портал был открыт.
        """
        if "closed_portal" in self.tokens:
            self.tokens.remove("closed_portal")
            self.open_portal = True
            logger.info(f"[Hall] Портал открыт в зале '{self.id}'")
            return True
        return False

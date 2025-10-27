from enum import Enum

class WSEvent(str, Enum):
    """Единый перечень WebSocket-событий в игре."""

    # системные / служебные
    PING = "ping"
    STATE_UPDATE = "state_update"
    ACTION_PERFORMED = "action_performed"
    LOG_ENTRY = "log_entry"

    # игровой процесс
    GAME_STARTED = "game_started"
    TURN_ENDED = "turn_ended"
    GAME_OVER = "game_over"

    # взаимодействие с игроками
    CHOOSE_DISCARD = "choose_discard"
    CARD_DISCARDED = "card_discarded"

    # действия героев и монстров
    MOVE = "move"
    ATTACK = "attack"
    TREASURE_EFFECT = "treasure_effect"

    # системные уведомления
    ERROR = "error"
    INFO = "info"

    # отслеживание стадий
    PHASE_CHANGED = "phase_changed"

    @classmethod
    def list(cls):
        """Список всех доступных событий (удобно для логирования и дебага)."""
        return [e.value for e in cls]


# models/enums.py
from enum import Enum


class PhaseType(str, Enum):
    """
    Текущая фаза игры.
    """
    SETUP = "setup"         # подготовка партии
    PLAYER = "player"       # ход игрока
    HEROES = "heroes"       # ход героев (нашествие)
    GAME_OVER = "game_over" # завершение партии


class DifficultyType(str, Enum):
    """
    Уровень сложности — влияет на количество карт гильдии,
    разыгрываемых в каждой волне (см. PhaseManager).
    """
    FAMILY = "family"       # семейный режим
    PROBLEM = "problem"     # проблемный
    HARD = "hard"           # тяжёлый


class CardType(str, Enum):
    """
    Типы карт в игре.
    """
    MONSTER = "monster"
    LOOT = "loot"
    HERO = "hero"
    SCENARIO = "scenario"
    CLAN_HINT = "clan_hint"


class LootType(str, Enum):
    """
    Типы добычи (магазинных карт).
    """
    WEAPON = "weapon"
    PET = "pet"
    POTION = "potion"
    SCROLL = "scroll"


class HeroType(str, Enum):
    """
    Типы героев гильдии.
    """
    WARRIOR = "warrior"
    MAGE = "mage"
    ARCHER = "archer"
    THIEF = "thief"


class TokenType(str, Enum):
    """
    Различные жетоны, встречающиеся в комнатах.
    """
    TRAP = "trap"
    TREASURE = "treasure"
    PORTAL = "portal"
    RESOURCE = "resource"


class ActionType(str, Enum):
    """
    Типы действий игрока (используется в PlayerAction).
    """
    PLAY_CARD = "play_card"
    MOVE_MONSTER = "move_monster"
    ATTACK = "attack"
    DEFEND = "defend"
    BUY_CARD = "buy_card"
    DISCARD_CARD = "discard_card"
    REACTION = "reaction"


class ReactionType(str, Enum):
    """
    Типы реакций (используется в ActionService.process_reaction()).
    """
    DEFENSE = "defense"
    INTERRUPT = "interrupt"
    BOOST = "boost"


class TreasureEffect(str, Enum):
    """
    Возможные эффекты сокровищ при краже.
    """
    ROBBERY = "robbery"     # грабёж — сброс ресурса из зала
    CURSE = "curse"         # проклятие — игроки сбрасывают карту
    HEAL = "heal"           # лечение — герои активируются
    PRISONER = "prisoner"   # пленник — герой в темницу
    DEFEAT = "defeat"       # похищено главное сокровище — поражение


class GameResult(str, Enum):
    """
    Итог партии.
    """
    VICTORY = "victory"
    DEFEAT = "defeat"
    IN_PROGRESS = "in_progress"

from enum import Enum
from typing import List


class FactionsWW(Enum):
    """A faction is a group of players that share the same goal."""

    COUPLE = "Love Couple"
    ABOMINABLE_SECTARIAN = "Abominable Sectarian"
    SPIRIT = "Spirit"
    WHITE_WOLF = "White Wolf"
    WEREWOLVES = "Werewolves"
    VILLAGE = "Village"
    MERCENARY = "Mercenary"
    ANGEL = "Angel"
    THIEF = "Thief"

    def __repr__(self):
        return self.value

    def __str__(self):
        return self.value

LIST_FACTIONS_BY_PRIORITY: List[FactionsWW] = [
    FactionsWW.COUPLE,
    FactionsWW.ABOMINABLE_SECTARIAN,
    FactionsWW.SPIRIT,
    FactionsWW.WHITE_WOLF,
    FactionsWW.WEREWOLVES,
    FactionsWW.VILLAGE,
    FactionsWW.MERCENARY,
    FactionsWW.ANGEL,
    FactionsWW.THIEF,
]
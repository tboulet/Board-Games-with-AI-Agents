from enum import Enum
from typing import List


class FactionsWW(Enum):
    """A faction is a group of players that share the same goal.
    
    These are represented with strings.
    Additionnally, any faction should be in the list LIST_FACTIONS_BY_PRIORITY, which is a list of factions ordered by priority.
    The first factions in the list have priority over the last ones.
    This means a player in a faction with high priority cannot change towards a faction with lower priority (unless specific cases)
    and will conserve its faction.
    """

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
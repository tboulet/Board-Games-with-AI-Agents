from typing import List
from boardgames.games.werewolves.phase.base_phase import Phase
from boardgames.games.werewolves.roles.base_role import RoleWW





LIST_PHASES_WW_ORDERED: List[Phase] = [
    # Phase.DAY_SPEECH,
    # Phase.DAY_VOTE,
    # Phase.VICTORY_CHECK,
    # Phase.JUDGE_PHASE,
    # Phase.MERCENARY_CHECK,
    # Phase.ANGEL_CHECK,
    # Phase.WOLFDOG_CHOICE,
    # Phase.SISTER_SPEECH,
    # Phase.PYROMANCER_PHASE,  # Phases after can be skipped by the pyromancer malus
    # Phase.BEAR_SHOWMAN_PHASE,
    # Phase.FOX_PHASE,
    # Phase.THIEF_PHASE,
    # Phase.SEER_PHASE,
    # Phase.SAVIOR_PHASE,
    # Phase.NECROMANCER_PHASE,
    # Phase.NIGHT_WOLF_SPEECH,
    # Phase.NIGHT_WOLF_VOTE,
    # Phase.PERFIDIOUS_WOLF_ATTACK,
    # Phase.INFECTION_PHASE,
    # Phase.WHITE_WOLF_ATTACK,
    # Phase.WITCH_PHASE,
    # Phase.CROW_PHASE,
    # Phase.INVISIBLE_PHASE,
]

# class Phase(str, Enum):
#     DAY_SPEECH = "Day Speech"
#     DAY_VOTE = "Day Vote"
#     VICTORY_CHECK = "Victory Check"
#     SAVIOR_PHASE = "Savior Phase"
#     NIGHT_WOLF_SPEECH = "Night Wolf Speech"
#     NIGHT_WOLF_VOTE = "Night Wolf Vote"
#     INFECTION_PHASE = "Infection Phase"
#     WHITE_WOLF_ATTACK = "White Wolf Attack"
#     SEER_PHASE = "Seer Phase"
#     WITCH_PHASE = "Witch Phase"
#     HUNTER_CHOICE = "Hunter Choice"
#     GRAVEDIGGER_CHOICE = "Gravedigger Choice"
#     NECROMANCER_PHASE = "Necromancer Phase"
#     THIEF_PHASE = "Thief Phase"
#     CROW_PHASE = "Crow Phase"
#     INVISIBLE_PHASE = "Invisible Phase"
#     PERFIDIOUS_WOLF_ATTACK = "Perfidious Wolf Attack"
#     MERCENARY_CHECK = "Mercenary Check"
#     PYROMANCER_PHASE = "Pyromancer Phase"
#     ANGEL_CHECK = "Angel Check"
#     WOLFDOG_CHOICE = "Wolfdog Choice"
#     JUDGE_PHASE = "Judge Phase"
#     BEAR_SHOWMAN_PHASE = "Bear Showman Phase"
#     FOX_PHASE = "Fox Phase"
#     SISTER_SPEECH = "Sister Speech"

from typing import List
from boardgames.games.werewolves.factions import FactionsWW
from boardgames.games.werewolves.identity import Identity
from boardgames.games.werewolves.statutes.base_status import Status
from boardgames.games.werewolves.roles.base_role import RoleWW
from boardgames.games.werewolves.phase.base_phase import Phase


class RoleCrow(RoleWW):

    @classmethod
    def get_name(cls) -> str:
        return "Crow"

    def get_initial_faction(self) -> FactionsWW:
        return FactionsWW.VILLAGE

    def get_initial_statutes(self) -> List[Status]:
        return []

    def get_associated_phases(self) -> List[str]:
        return [Phase.CROW_PHASE]

    def get_textual_description(self) -> str:
        return "The crow is a player that designates one player each night. This player will receive 2 additional votes during the day."


class RoleWhiteWolf(RoleWW):

    @classmethod
    def get_name(cls) -> str:
        return "White Wolf"

    def get_initial_faction(self) -> FactionsWW:
        return FactionsWW.WHITE_WOLF

    def get_initial_statutes(self) -> List[Status]:
        return [Status.IS_WOLF, Status.IS_SOLO]

    def get_associated_phases(self) -> List[str]:
        return [Phase.WHITE_WOLF_ATTACK]

    def get_textual_description(self) -> str:
        return (
            "The white wolf is a member of the wolves that is secretely a traitor and that must win alone."
            "Your power are : \n"
            "- one night out of two, you can choose a player to eliminate."
        )


class RolePyromancer(RoleWW):

    @classmethod
    def get_name(cls) -> str:
        return "Pyromancer"

    def get_initial_faction(self) -> FactionsWW:
        return FactionsWW.VILLAGE

    def get_initial_statutes(self) -> List[Status]:
        return []

    def get_associated_phases(self) -> List[str]:
        return [Phase.PYROMANCER_PHASE]

    def get_textual_description(self) -> str:
        return "The pyromancer is a villager that can each night choose a player that won't be able to use its power this night day."

    def get_exception_phases(self) -> List[Phase]:
        """Return a list of phases that won't be skipped by the pyromancer malus, for convenience."""
        return [
            Phase.DAY_SPEECH,
            Phase.DAY_VOTE,
            Phase.NIGHT_WOLF_SPEECH,
            Phase.NIGHT_WOLF_VOTE,
            Phase.INVISIBLE_PHASE,
        ]


ROLES_EXTENSION_VILLAGE = {
    RoleCrow.get_name(): RoleCrow,
    RoleWhiteWolf.get_name(): RoleWhiteWolf,
    RolePyromancer.get_name(): RolePyromancer,
}

from typing import List
from boardgames.games.werewolves.factions import FactionsWW
from boardgames.games.werewolves.phase.base_phase import Phase
from boardgames.games.werewolves.state import StateWW
from boardgames.games.werewolves.roles.base_role import RoleWW
from boardgames.games.werewolves.statutes.base_status import Status
from boardgames.types import JointAction



class RoleThief(RoleWW):

    @classmethod
    def get_name(cls) -> str:
        return "Thief"

    def get_initial_faction(cls) -> FactionsWW:
        return FactionsWW.THIEF

    def get_initial_statutes(self) -> List[Status]:
        return [Status.HAS_THIEF_POWER, Status.IS_SOLO]

    def get_associated_phases(self) -> List[str]:
        return [Phase.THIEF_PHASE]

    @classmethod
    def get_textual_description(cls) -> str:
        return (
            "The thief is a player that can steal the role of another player once he dies."
            "Your power are : \n"
            "- once per game, you can choose a player to steal his role when he dies. When he dies, you will become this role."
        )


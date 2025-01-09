from collections import defaultdict
import random
from typing import List, Tuple
from boardgames.games.werewolves.factions import FactionsWW
from boardgames.games.werewolves.phase.base_phase import Phase
from boardgames.games.werewolves.roles.base_role import RoleWW
from boardgames.games.werewolves.state import StateWW, StatusIsWolf
from boardgames.games.werewolves.statutes.base_status import Status
from boardgames.types import JointAction
from boardgames.action_spaces import FiniteActionSpace, JointActionSpace
from boardgames.types import InfoDict, JointAction, JointObservation, JointPlayingInformation, JointReward, State, TerminalSignal

      
class RoleVillager(RoleWW):
    @classmethod
    def get_name(cls) -> str:
        return "Villager"

    def get_initial_faction(self) -> FactionsWW:
        return FactionsWW.VILLAGE

    def get_initial_statutes(self) -> List[Status]:
        return []

    def get_associated_phases(self) -> List[str]:
        return []

    def get_textual_description(self) -> str:
        return "The villagers are the majority of the players. They have no particular power, and must use their wits to find the werewolves."

    def initialize_role(self, state):
        pass

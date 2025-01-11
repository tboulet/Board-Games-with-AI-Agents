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
from boardgames.types import (
    InfoDict,
    JointAction,
    JointObservation,
    JointPlayingInformation,
    JointReward,
    State,
    TerminalSignal,
)


class RoleVillager(RoleWW):
    @classmethod
    def get_name(cls) -> str:
        return "Villager"

    @classmethod
    def get_initial_faction(cls) -> FactionsWW:
        return FactionsWW.VILLAGE

    def get_initial_statutes(self) -> List[Status]:
        return []

    def get_associated_phases(self) -> List[str]:
        return []

    @classmethod
    def get_textual_description(cls) -> str:
        return (
            "Role : Villager. Your objective is to identify and eliminate all the Werewolves hidden among the players. "
            "You have no special abilities, so you must rely on logic, observation, and social deduction to survive and help your team. "
            "During the Day Phase, you will listen to other players, analyze their behavior, and participate in discussions to uncover suspicious actions. "
            "You will then vote to eliminate the player you believe is most likely a Werewolf. "
            "At night, you take no action and must trust that the special roles will help protect the village. "
            "Winning Condition: You win when all the Werewolves have been eliminated. "
            "Strategic Tips: "
            "- Pay close attention to how players speak and behave. Inconsistencies may reveal hidden Werewolves. "
            "- Work with others, but be cautious—anyone could be lying. "
            "- Use your vote wisely. A wrong decision could eliminate an innocent player and help the Werewolves. "
            "Stay alert, think critically, and help guide the village to victory."
        )

    @classmethod
    def get_short_textual_description(cls) -> str:
        return "The base villager role. Must use their wits to find the werewolves."

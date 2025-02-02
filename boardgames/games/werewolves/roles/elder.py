from collections import defaultdict
import random
from typing import List, Tuple
from boardgames.games.werewolves.causes_of_deaths.base_cause import CauseOfDeath
from boardgames.games.werewolves.factions import FactionsWW
from boardgames.games.werewolves.phase.base_phase import Phase
from boardgames.games.werewolves.roles.base_role import RoleWW
from boardgames.games.werewolves.state import CauseWolfAttack, StateWW, StatusIsWolf
from boardgames.games.werewolves.statutes.base_status import Status, StatusBaseProtection
from boardgames.types import JointAction
from boardgames.action_spaces import (
    FiniteActionSpace,
    JointActionSpace,
    TextualActionSpace,
)
from boardgames.types import (
    InfoDict,
    JointAction,
    JointObservation,
    JointPlayingInformation,
    JointReward,
    State,
    TerminalSignal,
)

class StatusProtectionElder(StatusBaseProtection):
    
    def get_name(self) -> str:
        return "Protection Elder"
    
    def apply_protection_status(
        self,
        state: StateWW,
        id_player: int,
    ) -> bool:
        # Get the causes that need to be removed
        causes_of_deaths = state.night_attacks.get(id_player, set())
        causes_to_remove = []
        for c in causes_of_deaths:
            if isinstance(c, CauseWolfAttack):
                state.common_obs.log(
                    f"[!] Elder protection was usefull for protection of player {id_player}.",
                    "INFO",
                )
                causes_to_remove.append(c)
                # Remove the protection status
                state.identities[id_player].remove_status(self)
        # Remove the causes that need to be removed
        for c in causes_to_remove:
            if isinstance(c, CauseWolfAttack):
                state.night_attacks[id_player].remove(c)
    
    
    
class RoleElder(RoleWW):
    @classmethod
    def get_name(cls) -> str:
        return "Elder"
    
    @classmethod
    def get_initial_faction(cls) -> FactionsWW:
        return FactionsWW.VILLAGE

    def get_initial_statutes(self) -> List[Status]:
        return [StatusProtectionElder()]
    
    def get_associated_phases(self) -> List[Phase]:
        return []

    @classmethod
    def get_textual_description(cls) -> str:
        return (
            "Role: Elder. Your objective is to help the Villagers eliminate all the Werewolves while using your special ability to protect yourself and others. "
            "As an Elder, you have a unique protection against Werewolf attacks. If a Werewolf targets you during the Night Phase, the attack will fail, and you will survive. "
            "This protection can be a key advantage, especially when the Werewolves are trying to eliminate important players. "
            "During the Day Phase, you are just like a normal Villager, participating in discussions and voting. "
            "You must be strategic in how you use your immunity—while it protects you from Werewolves, you still need to contribute to the village's efforts to identify and eliminate the Werewolves. "
            "Winning Condition: You win when all the Werewolves are eliminated. "
            "Strategic Tips: "
            "- Use your immunity to stay alive and provide valuable input without being too obvious about your role. "
            "- You are a key target for the Werewolves because of your protection, so avoid drawing attention to yourself too early. "
            "- Help the Villagers identify Werewolves and use your survival to steer the vote in the right direction. "
            "- Protect your immunity by not acting too suspiciously and guiding the village without giving away your special role. "
            "With your protection, you are a strong asset to the village—stay smart and lead the charge against the Werewolves."
        )
        
    @classmethod
    def get_short_textual_description(cls):
        return "Survive one werewolf attack."

from collections import defaultdict
import random
from typing import List, Tuple
from boardgames.games.werewolves.causes_of_deaths.base_cause import CauseOfDeath
from boardgames.games.werewolves.factions import FactionsWW
from boardgames.games.werewolves.phase.base_phase import Phase
from boardgames.games.werewolves.roles.base_role import RoleWW
from boardgames.games.werewolves.state import CauseVote, StateWW, StatusCannotVote, StatusIsWolf
from boardgames.games.werewolves.statutes.base_status import Status
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


class StatusVillageFoolProtection(Status):
    
    def get_name(self) -> str:
        return "Village Fool Protection"
    
    def apply_death_announcement_and_confirm(
        self, state: StateWW, id_player: int, cause: CauseOfDeath
    ) -> bool:
        if cause == CauseVote():
            # Remove the protection status
            state.identities[id_player].remove_status(self)
            # Remove the vote right
            state.identities[id_player].add_status(StatusCannotVote())
            # Inform the village fool and the village
            state.common_obs.add_message(
                "You have been voted by the village for this day. Thanks to your role, you are still alive but can't vote anymore.",
                idx_player=id_player,
            )
            state.common_obs.add_global_message(
                f"Player {id_player} has been voted by the village but is the Village Fool. They are still alive but can't vote anymore."
            )
            # Return False to prevent the death of the player
            return False
        else:
            return True

class RoleVillageFool(RoleWW):
    
    @classmethod
    def get_name(cls) -> str:
        return "Village Fool"
    
    @classmethod
    def get_initial_faction(cls) -> FactionsWW:
        return FactionsWW.VILLAGE

    def get_initial_statutes(self) -> List[Status]:
        return [StatusVillageFoolProtection()]

    def get_associated_phases(self) -> List[Phase]:
        return []

    @classmethod
    def get_textual_description(cls) -> str:
        return (
            "Role: Village Fool. Your objective is to survive while being eliminated by the Villagers during the vote. "
            "If you are voted out by the Villagers, you do not die, but your role is immediately revealed publicly, and you can no longer participate in voting. "
            "Even though you are no longer allowed to vote, you are still part of the Village faction, and your goal remains the same: help eliminate the Werewolves. "
            "During the Day Phase, your task is to behave in a way that does not draw suspicion while still influencing the discussions. "
            "You want to be perceived as a Villager, but not too powerful, or you risk being voted out too early. "
            "If you are voted out, you become a revealed Villager who no longer has the power to vote but can still interact with the other players. "
            "Winning Condition: You win if all the Werewolves are eliminated, but you can no longer vote if you are eliminated. "
            "Strategic Tips: "
            "- Try to remain neutral and avoid drawing too much attention to yourself. If you act too suspiciously, the Villagers might vote you out prematurely. "
            "- Be subtle and don’t try to manipulate votes aggressively; instead, try to stay in the game by helping the Village without revealing your true role. "
            "- Once eliminated, you still remain a Villager, but with no voting power. Ensure your influence on the discussions is still felt despite your reduced role. "
            "- Avoid being eliminated too early in the game; your value is as a Villager, so play carefully and strategically. "
            "The Village Fool's ultimate victory comes when the Werewolves are gone, even if you're no longer able to vote."
        )
        
    @classmethod
    def get_short_textual_description(cls):
        return "Survive if voted out by the village, but lose the ability to vote."

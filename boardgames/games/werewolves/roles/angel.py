from collections import defaultdict
import random
from typing import List, Tuple
from boardgames.games.werewolves.causes_of_deaths.base_cause import CauseOfDeath
from boardgames.games.werewolves.factions import FactionsWW
from boardgames.games.werewolves.phase.base_phase import Phase
from boardgames.games.werewolves.roles.base_role import RoleWW
from boardgames.games.werewolves.state import CauseVote, StateWW, StatusIsWolf
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


class StatusAngelActive(Status):
    
    def get_name(self) -> str:
        return "Angel Active"
    
    def apply_death_announcement_and_confirm(
        self, state: StateWW, id_player: int, cause: CauseOfDeath
    ) -> bool:
        # If angel dies on day 2 (turn 1), he wins the game
        if state.turn == 1:
            if cause == CauseVote():
                state.common_obs.add_global_message(
                    "The angel has been voted at the first vote. He wins the game.",
                )
                state.identities[id_player].role.is_win_condition_achieved = True
                return False
        return True
    

class PhaseAngelCheck(Phase):
        
    def get_name(self) -> str:
        return "Angel Check"
    
    def play_action(self, state: StateWW, joint_action: JointAction):
        raise ValueError("Angel Check should not play any action.")
    
    def return_feedback(self, state: StateWW) -> Tuple[
        JointReward,
        JointPlayingInformation,
        JointObservation,
        JointActionSpace,
        TerminalSignal,
        InfoDict,
    ]:
        # Skip phase at turn 0
        if state.turn <= 0:
            state.phase_manager.advance_phase()
            return
        # Check if the angel has been eliminated
        state.common_obs.add_message(
            "You have failed to be eliminated at the first vote. You are now a regular villager.",
            idx_player=self.id_player,
        )
        state.common_obs.log(
            f"[!] Angel {self.id_player} has failed to be eliminated at the first vote. He is now a regular villager.",
            "INFO",
        )
        # Change the angel into a villager
        state.identities[self.id_player].change_faction(FactionsWW.VILLAGE)
        state.identities[self.id_player].remove_status(StatusAngelActive())
        # Advance to the next phase
        state.phase_manager.advance_phase()
        state.phase_manager.remove_phase(self)
        return
        
    def is_day_phase(self) -> bool:
        return True


class RoleAngel(RoleWW):
    @classmethod
    def get_name(cls) -> str:
        return "Angel"

    @classmethod
    def get_initial_faction(cls) -> FactionsWW:
        return FactionsWW.ANGEL

    def get_initial_statutes(self) -> List[Status]:
        return [StatusAngelActive()]

    def get_associated_phases(self) -> List[Phase]:
        return [PhaseAngelCheck(id_player=self.id_player)]

    @classmethod
    def get_textual_description(self) -> str:
        return (
            "Role: Angel. Your objective is to get yourself eliminated during the first voting round on the **second day** to achieve victory. "
            "Unlike other roles, you do not belong to the Villagers or the Werewolves; your goal is entirely personal. "
            "If you are successfully voted out by the Villagers on the second day, you **immediately win the game**, regardless of the overall outcome. "
            "However, if you fail to get eliminated, you will lose your special ability and become a regular Villager, "
            "joining their objective to eliminate all the Werewolves. "
            "During the Day Phases, you must subtly influence the discussions to increase your chances of being voted out, "
            "without making yourself too obvious, which could make players suspicious of your intentions. "
            "During the Night Phases, you take no action and hope to survive until the crucial voting round. "
            "Winning Condition: You win if you are eliminated by the Villagers during the first vote on the second day. "
            "Strategic Tips: "
            "- Carefully manipulate conversations to subtly draw suspicion without raising doubts about your true objective. "
            "- Avoid making it too obvious that you want to be eliminated, as players may catch on and refuse to vote for you. "
            "- If you fail to achieve your goal, shift your strategy and work towards the Villagers' victory. "
            "Play carefully, mislead strategically, and achieve your unique win condition."
        )

        
    @classmethod
    def get_short_textual_description(cls):
        return "Win by being voted out by the Villagers on the first vote (second day). If not, become a regular Villager."

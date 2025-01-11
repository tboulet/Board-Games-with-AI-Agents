from collections import defaultdict
import random
from typing import List, Tuple
from boardgames.games.werewolves.factions import FactionsWW
from boardgames.games.werewolves.phase.base_phase import Phase
from boardgames.games.werewolves.roles.base_role import RoleWW
from boardgames.games.werewolves.state import StateWW, StatusIsWolf
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


class PhaseSeer(Phase):

    def get_name(self) -> str:
        return "Seer Phase"

    def play_action(self, state: StateWW, joint_action: JointAction) -> StateWW:
        id_target_seer: int = joint_action[self.id_player]
        assert id_target_seer in range(
            state.n_players
        ), f"Player {self.id_player} must choose a valid player to investigate, but chose {id_target_seer}."
        assert state.list_are_alive[
            id_target_seer
        ], f"Player {self.id_player} cannot investigate a dead player, but chose {id_target_seer}."
        role_name_target_seer = state.identities[
            id_target_seer
        ].role.get_appearance_name()
        state.common_obs.add_message(
            f"You have investigated player {id_target_seer}. You see their role is {role_name_target_seer}.",
            idx_player=self.id_player,
        )
        # Advance to the next phase
        state.phase_manager.advance_phase()
        return state

    def return_feedback(self, state: StateWW) -> Tuple[
        JointReward,
        JointPlayingInformation,
        JointObservation,
        JointActionSpace,
        TerminalSignal,
        InfoDict,
    ]:

        list_id_targets = state.get_list_id_players_alive()
        state.common_obs.add_message(
            f"Seer, you can now choose a player to investigate the role among the alive players : {list_id_targets}.",
            idx_player=self.id_player,
        )
        action_space = FiniteActionSpace(actions=list_id_targets)
        return state.get_return_feedback_one_player(
            id_player=self.id_player, action_space=action_space
        )

    def is_day_phase(self) -> bool:
        return False


class RoleSeer(RoleWW):
    @classmethod
    def get_name(cls) -> str:
        return "Seer"

    @classmethod
    def get_initial_faction(cls) -> FactionsWW:
        return FactionsWW.VILLAGE

    def get_initial_statutes(self) -> List[Status]:
        return []

    def get_associated_phases(self) -> List[str]:
        return [PhaseSeer(id_player=self.id_player)]

    @classmethod
    def get_textual_description(cls) -> str:
        return (
            "Role: Seer. Your objective is to help the Villagers identify and eliminate all the Werewolves. "
            "Each night, you can secretly choose one player to reveal their true role. This powerful ability allows you to gather crucial information to guide the village. "
            "During the Day Phase, you must decide how to use this information without revealing your identity, as Werewolves will try to eliminate you if they suspect who you are. "
            "Winning Condition: You win when all the Werewolves have been eliminated. "
            "Strategic Tips: "
            "- Be cautious when sharing information. Revealing too much can make you a target for the Werewolves. "
            "- Use subtle hints and suggestions to influence votes without exposing yourself. "
            "- If you discover a Werewolf, decide whether to directly accuse them or guide others to that conclusion. "
            "Balance secrecy and influence to protect yourself and lead the village to victory."
        )

    @classmethod
    def get_short_textual_description(cls) -> str:
        return "Watch the role of a player each night."

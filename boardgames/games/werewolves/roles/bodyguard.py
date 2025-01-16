from collections import defaultdict
import random
from typing import List, Set, Tuple
from boardgames.games.werewolves.causes_of_deaths.base_cause import CauseOfDeath
from boardgames.games.werewolves.factions import FactionsWW
from boardgames.games.werewolves.phase.base_phase import Phase
from boardgames.games.werewolves.roles.base_role import RoleWW
from boardgames.games.werewolves.state import CauseWolfAttack, StateWW, StatusIsWolf
from boardgames.games.werewolves.statutes.base_status import (
    Status,
    StatusBaseProtection,
)
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


class StatusProtectionBodyguard(StatusBaseProtection):
    """This status protects the player from any wolf based attack."""

    def get_name(self) -> str:
        return "Protection Bodyguard"

    def apply_protection_status(
        self,
        state: StateWW,
        id_player: int,
    ) -> Tuple[bool, Set[CauseOfDeath]]:
        # Get the causes that need to be removed
        causes_of_deaths = state.night_attacks.get(id_player, set())
        causes_to_remove = []
        for c in causes_of_deaths:
            if isinstance(c, CauseWolfAttack):
                state.common_obs.log(
                    f"[!] Bodyguard protection was usefull for protection of player {id_player}.",
                    "INFO",
                )
                causes_to_remove.append(c)
        # Remove the causes that need to be removed
        for c in causes_to_remove:
            if isinstance(c, CauseWolfAttack):
                state.night_attacks[id_player].remove(c)
        # Remove the protection status
        state.identities[id_player].remove_status(self)

class PhaseBodyguard(Phase):

    def __init__(self, id_player: int):
        self.id_last_player_protected = None
        super().__init__(id_player)

    def get_name(self) -> str:
        return "Bodyguard Phase"

    def play_action(self, state: StateWW, joint_action: JointAction):
        # Protect the player
        id_target_bodyguard: int = joint_action[self.id_player]
        self.id_last_player_protected = id_target_bodyguard
        state.common_obs.add_message(
            f"You have protected player {id_target_bodyguard}.",
            idx_player=self.id_player,
        )
        state.identities[id_target_bodyguard].add_status(StatusProtectionBodyguard())
        state.common_obs.log(
            f"[!] Bodyguard protected player {id_target_bodyguard}.",
            "ACTION",
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
        list_id_players_protected_candidates = [
            str(i)
            for i in range(state.n_players)
            if state.list_are_alive[i]
            and not state.identities[i].has_status(StatusProtectionBodyguard())
        ]
        # Inform the bodyguard of the players they can protect
        state.common_obs.add_message(
            f"Bodyguard, you can now choose a player to protect among the alive players : {list_id_players_protected_candidates}. You can't protect the same player as the previous night.",
            idx_player=self.id_player,
        )
        action_space = FiniteActionSpace(actions=list_id_players_protected_candidates)
        return state.get_return_feedback_one_player(
            id_player=self.id_player, action_space=action_space
        )

    def is_day_phase(self) -> bool:
        return False


class RoleBodyguard(RoleWW):

    @classmethod
    def get_name(cls) -> str:
        return "Bodyguard"

    @classmethod
    def get_initial_faction(cls) -> FactionsWW:
        return FactionsWW.VILLAGE

    def get_initial_statutes(self) -> List[Status]:
        return []

    def get_associated_phases(self) -> List[Phase]:
        return [PhaseBodyguard(id_player=self.id_player)]

    @classmethod
    def get_textual_description(cls) -> str:
        return (
            "Role: Bodyguard. Your objective is to protect the Villagers and help eliminate all the Werewolves. "
            "Each night, you can choose one player to protect from being eliminated by the Werewolves. If the Werewolves target that player, their attack will fail. "
            "However, you **cannot protect the same player two nights in a row**, so you must carefully decide who to defend each night. "
            "During the Day Phase, you participate in discussions and voting like any other Villager, blending in to avoid being targeted by the Werewolves. "
            "Winning Condition: You win when all the Werewolves are eliminated. "
            "Strategic Tips: "
            "- You can protect yourself, which can be useful in order to stay alive and continue protecting others. "
            "- Pay close attention to the flow of discussions and voting to identify who might be targeted by the Werewolves. "
            "- Protect key players, such as the Seer or Witch, but remember you cannot guard the same player on consecutive nights. "
            "- Avoid revealing your role, as the Werewolves may prioritize eliminating you to remove your protection. "
            "- Balance protecting others with the risk of leaving yourself vulnerable. "
            "Use your protection wisely to shield important allies and guide the village to victory."
        )

    @classmethod
    def get_short_textual_description(cls):
        return "Protect a player each night from the werewolves' attack (can't protect the same player two nights in a row)."

from collections import defaultdict
import random
from typing import List, Tuple
from boardgames.games.werewolves.causes_of_deaths.base_cause import CauseOfDeath
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


class CauseHunterShot(CauseOfDeath):
    def get_name(self) -> str:
        return "Hunter Shot"

    def is_day_cause_of_death(self):
        return True

    def get_message_on_death(self, state, id_player):
        return f"Player {id_player} was shot by the Hunter."


class PhaseHunter(Phase):

    def get_name(self) -> str:
        return "Hunter Phase"

    def play_action(self, state: StateWW, joint_action: JointAction):
        id_target_hunter: int = joint_action[self.id_player]
        state.common_obs.add_message(
            f"You have eliminated player {id_target_hunter}.",
            idx_player=self.id_player,
        )
        state.common_obs.add_global_message(
            f"The Hunter has decided to eliminate player {id_target_hunter}."
        )
        state.common_obs.log(
            f"Hunter {self.id_player} has eliminated player {id_target_hunter}.",
            "ACTION",
        )
        state.apply_death_consequences(id_target_hunter, CauseHunterShot())
        # Advance to the next phase
        state.phase_manager.advance_phase()
        # Self destruct the phase
        state.phase_manager.remove_phase(self)

    def return_feedback(self, state: StateWW) -> Tuple[
        JointReward,
        JointPlayingInformation,
        JointObservation,
        JointActionSpace,
        TerminalSignal,
        InfoDict,
    ]:
        list_id_players_target_candidate = state.get_list_id_players_alive()
        state.common_obs.add_message(
            f"Hunter, you are dead, but can shot a final bullet before leaving the village. Choose a player to kill among the alive players : {list_id_players_target_candidate}.",
            idx_player=self.id_player,
        )
        state.common_obs.add_global_message(
            f"The Hunter is dead. Before leaving, he will be able to eliminate a player right before the night phase.",
            except_idx=self.id_player,
        )
        action_space = FiniteActionSpace(actions=list_id_players_target_candidate)
        return state.get_return_feedback_one_player(id_player=self.id_player, action_space=action_space
        )

    def is_day_phase(self) -> bool:
        return False


class RoleHunter(RoleWW):
    @classmethod
    def get_name(cls) -> str:
        return "Hunter"

    @classmethod
    def get_initial_faction(cls) -> FactionsWW:
        return FactionsWW.VILLAGE

    def get_initial_statutes(self) -> List[Status]:
        return []

    def get_associated_phases(self) -> List[str]:
        return []

    @classmethod
    def get_textual_description(self) -> str:
        return (
            "Role: Hunter. Your objective is to help the Villagers eliminate all the Werewolves. "
            "If you are eliminated—either by being voted out during the Day Phase or killed during the Night Phase—you have the ability to immediately shoot and eliminate another player of your choice. "
            "This ability is extremely powerful and can change the course of the game, so choosing your target wisely is critical. "
            "Pay close attention to players' behavior, accusations, and voting patterns to identify who might be a Werewolf. "
            "A wrong decision could result in eliminating an innocent Villager, giving the Werewolves a significant advantage. "
            "Winning Condition: You win when all the Werewolves are eliminated. "
            "Strategic Tips: "
            "- Constantly observe how players interact, vote, and defend themselves to identify suspicious behavior. "
            "- Have a clear idea of who you would target if you are eliminated. This decision should be based on logic and evidence, not emotion. "
            "- Be careful not to reveal your role too early, as Werewolves may try to eliminate you to prevent you from using your ability effectively. "
            "- If you are about to be eliminated, use your shot strategically to weaken the Werewolf team or eliminate a key threat. "
            "Your final shot can turn the game in favor of the Villagers—stay sharp, think critically, and make it count."
        )
        
    @classmethod
    def get_short_textual_description(cls):
        return "Can shoot a player when eliminated."

    # Specific method for the hunter role : insert the hunter phase
    def apply_death_consequences(self, state: StateWW, id_player: int, cause: CauseOfDeath):
        state.phase_manager.insert_phase(PhaseHunter(id_player=self.id_player))
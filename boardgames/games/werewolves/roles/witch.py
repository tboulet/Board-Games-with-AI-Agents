from collections import defaultdict
import random
from typing import List, Tuple
from boardgames.games.werewolves.causes_of_deaths.base_cause import CauseOfDeath
from boardgames.games.werewolves.factions import FactionsWW
from boardgames.games.werewolves.phase.base_phase import Phase
from boardgames.games.werewolves.roles.base_role import RoleWW
from boardgames.games.werewolves.state import CauseWolfAttack, StateWW, StatusIsWolf
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


class CauseKillPotion(CauseOfDeath):
    def get_name(self) -> str:
        return "Kill potion"

    def is_day_cause_of_death(self):
        return False


class PhaseWitch(Phase):

    def get_name(self) -> str:
        return "Witch phase"

    def play_action(self, state: StateWW, joint_action: JointAction):
        action_witch: str = joint_action[self.id_player]
        role_witch: "RoleWitch" = state.identities[self.id_player].role
        if action_witch == "Do nothing":
            state.common_obs.add_message(
                "You have decided to not use any potion this night. ",
                idx_player=self.id_player,
            )
        elif action_witch == "Save":
            assert state.night_attacks, "No player to save."
            role_witch.has_save_potion = False
            id_player_victim = state.get_ids_wolf_victims(state)[0]
            for cause_of_death_wolf in [
                CauseWolfAttack(),
            ]:
                state.night_attacks[id_player_victim].remove(cause_of_death_wolf)
            state.common_obs.add_message(
                f"You have chosen to use your save potion on player {id_player_victim}.",
                idx_player=self.id_player,
            )
        elif action_witch.startswith("Kill"):
            role_witch.has_kill_potion = False
            id_target_witch = int(action_witch.split(" ")[1])
            state.night_attacks[id_target_witch].add(CauseKillPotion())
            state.common_obs.add_message(
                f"You have chosen to use your kill potion on player {id_target_witch}.",
                idx_player=self.id_player,
            )
        else:
            raise ValueError(f"Invalid action for the witch : {action_witch}.")
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
        role_witch: "RoleWitch" = state.identities[self.id_player].role
        # If the witch has no more potions, skip the phase
        if not role_witch.has_save_potion and not role_witch.has_kill_potion:
            state.common_obs.add_message(
                "You have no more potions to use this night. ",
                idx_player=self.id_player,
            )
            state.phase_manager.advance_phase()
            phase = state.phase_manager.get_current_phase()
            return phase.return_feedback(state)
        # Inform the witch its turn is starting
        state.common_obs.add_message(
            (
                f"Witch, you can now use one of your potions if you have any. "
                f"You can also choose to do nothing and keep your potions for later use with action 'Do nothing'. "
            ),
            idx_player=self.id_player,
        )
        list_actions = ["Do nothing"]
        # Get the wolf victim and inform the witch of it
        ids_wolf_victims = state.get_ids_wolf_victims()
        assert (
            len(ids_wolf_victims) <= 1
        ), "There should be at most one wolf victim. (Not implemented yet)"
        if len(ids_wolf_victims) == 1:
            id_wolf_victim = ids_wolf_victims[0]
            state.common_obs.add_message(
                f"You see the victim of the wolves is player {id_wolf_victim}. You can choose to save them by consuming your healing potion with action 'Save'.",
                idx_player=self.id_player,
            )
        else:
            state.common_obs.add_message(
                f"You see there is no victim of the wolves this night.",
                idx_player=self.id_player,
            )
        # Propose the witch to save the wolf victim (if any, and if the witch has the healing potion)
        if role_witch.has_save_potion and len(ids_wolf_victims) >= 1:
            list_actions.append("Save")
        # Propose the witch to choose a player to kill (if the witch has the death potion)
        if role_witch.has_kill_potion:
            list_actions_kill = []
            for i in range(self.n_players):
                if (
                    state.list_are_alive[i]
                    and (i != self.id_player)
                    and (
                        i not in ids_wolf_victims
                    )  # maybe remove this line to authorize the witch to kill the wolf victim, which in some case may survive the wolf attack (usefull in very rare cases)
                ):
                    list_actions_kill.append(f"Kill {i}")
            if len(list_actions_kill) > 0:
                list_actions.extend(list_actions_kill)
                state.common_obs.add_message(
                    (
                        f"You can choose to kill a player with action 'Kill <player_id>' by consuming your killing potion. "
                    ),
                    idx_player=self.id_player,
                )
        # Return feedback to the witch
        action_space = FiniteActionSpace(actions=list_actions)
        return state.get_return_feedback_one_player(
            id_player=self.id_player, action_space=action_space
        )

    def is_day_phase(self) -> bool:
        return False


class RoleWitch(RoleWW):

    def __init__(self):
        self.has_save_potion = True
        self.has_kill_potion = True
        super().__init__()

    @classmethod
    def get_name(cls) -> str:
        return "Witch"

    def get_initial_faction(cls) -> FactionsWW:
        return FactionsWW.VILLAGE

    def get_initial_statutes(self) -> List[Status]:
        return []

    def get_associated_phases(self) -> List[str]:
        return [PhaseWitch(id_player=self.id_player)]

    @classmethod
    def get_textual_description(cls) -> str:
        return (
            "Role: Witch. Your objective is to help the Villagers eliminate all the Werewolves while using your unique powers to protect the village. "
            "You have two potions at your disposal: the Healing Potion and the Poison Potion. Each potion can only be used **once** during the game, so choose wisely when to use them. "
            "The Healing Potion allows you to save a player from elimination, while the Poison Potion allows you to eliminate a player. Once you have used either potion, it is gone for the rest of the game. "
            "During the Night Phase, you must decide whether to use one of your potions or to save them for later, but keep in mind that both potions are limited resources. "
            "During the Day Phase, you must blend in to avoid drawing suspicion, as Werewolves may target you if they realize you are the Witch. "
            "Winning Condition: You win when all the Werewolves are eliminated. "
            "Strategic Tips: "
            "- The Healing Potion should be used to protect a key player, such as the Seer, if you believe they are at risk of being eliminated. "
            "- The Poison Potion can be used to eliminate a player you strongly suspect is a Werewolf, but be careful—an innocent death could harm the village. "
            "- Once a potion is used, it cannot be reused, so think carefully about the right moment for each. "
            "Manage your potions wisely, act strategically, and help the village secure victory."
        )

    @classmethod
    def get_short_textual_description(cls) -> str:
        return "Can use a healing potion (save wolves' victim) and a death potion (kill a player) once during the game."

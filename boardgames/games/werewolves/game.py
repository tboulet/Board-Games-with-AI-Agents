from abc import ABC, abstractmethod
from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
import random
from typing import Dict, List, Optional, Set, Tuple, Type, Union
import numpy as np
from boardgames.games.base_game import BaseGame
from boardgames.games.base_text_game import BaseTextBasedGame
from boardgames.games.werewolves.causes_of_deaths.base_cause import CauseOfDeath
from boardgames.games.werewolves.factions import FactionsWW
from boardgames.games.werewolves.phase.base_phase import Phase
from boardgames.types import (
    State,
    Observation,
    JointObservation,
    Action,
    JointAction,
    Reward,
    JointReward,
    PlayingInformation,
    JointPlayingInformation,
    InfoDict,
    TerminalSignal,
    AgentID,
)
from boardgames.action_spaces import (
    ActionsSpace,
    JointActionSpace,
    FiniteActionSpace,
    K_AmongFiniteActionSpace,
    TextualActionSpace,
)
from boardgames.utils import str_to_literal
from .state import StateWW
from .roles.base_role import RoleWW

from .roles.original import *
from .roles.extension_village import *
from .roles.extension_new_moon import *
from .roles.extension_personnages import *
from .roles.extension_wolfy import *
from .roles.extension_invisibles import *

from .roles.dict_roles import ROLES_CLASSES_WW


class WerewolvesGame(BaseTextBasedGame):

    def __init__(
        self,
        n_players: int,
        compo: Dict[str, dict],
        **kwargs,
    ) -> None:
        # Initialize the board game constants
        self.n_players = n_players
        self.compo = compo
        self.config = kwargs

    def get_game_context(self) -> str:
        compo_pretty = {k: v["n"] for k, v in self.compo.items()}
        compo_description = "Composition of the game:\n"
        for role_name, n in compo_pretty.items():
            RoleClass = ROLES_CLASSES_WW[role_name]
            if n == 1:
                compo_description += f"- {role_name} : {RoleClass.get_short_textual_description()}\n"
            elif n > 1:
                compo_description += f"- {role_name} ({n} times) : {RoleClass.get_short_textual_description()}\n"
        context = f"""
You will play a game of Werewolf. 

[GAME DESCRIPTION]
The game is set in a village where some players are secretly Werewolves. It is a social deduction game that requires logic, strategy, and deception.
It consists of a group of {self.n_players} players divided into two main factions: Villagers and Werewolves. 
- **Villagers** must identify and eliminate all the Werewolves.  
- **Werewolves** must secretly eliminate Villagers until none remain.  

The game alternates between two phases:
1. **Day Phase (Public Discussion and Voting):**  
   - Players express their suspicions or defend themselves in **one sentence**, in a **random order**. Players must balance logic and persuasion to influence the group's decision.  
   - All players then **vote simultaneously** to eliminate a player. In the case of a tie, the eliminated player is **randomly selected** among those tied.
2. **Night Phase (Secret Actions):**  
   - All players "close their eyes."  
   - **Werewolves** secretly wake up, discuss in turn, and select one player to eliminate.  
   - **Special roles** (e.g., Seer, Witch) may also act during this phase.

[COMPOSITION OF THE GAME] 
This is the composition of the game. You should pay attention to which roles are present since this could influence your strategy.
{compo_description}

Victory Conditions:
- Villagers win when all the Werewolves are eliminated.
- Werewolves win when all the Villagers are eliminated.

[STRATEGIC GUIDELINES]  
- **Werewolves** must deceive, mislead, and influence the voting without appearing suspicious. Balance between being too quiet and too aggressive.  
- **Villagers** must observe player behavior, detect inconsistencies, and vote logically.  
- Adapt your strategy as the game progresses—stay flexible and react to new information.  

[DECISION-MAKING TIPS]  
- **Analyze player behavior:** Look for contradictions and emotional cues.  
- **Manage risk:** Weigh the consequences of accusing or defending others.  
- **Control the narrative:** Guide discussions subtly to protect allies or frame opponents. 

Trust no one completely, observe carefully, adapt and survive to achieve your faction's goal.


[ANSWER FORMAT]
You are playing a textual board game. Your outputs must conform to the following rules:
1. Your **reasoning** should explain your thought process in natural language. Only you can see this.
2. Your **action** must be a valid action among those specified in the list of available actions. This determines how you will act/speak in the game.
   
Always separate your reasoning from your action. Your final output should explicitly label "Reasoning" and "Action," and the action must appear on a new line.
The action space (how should you formalize your answer) will be given to you at needed time.
Example:
Reasoning:
I chose this action because...
Action:
3

Good luck!
        """
        return context

    def reset(
        self,
    ) -> Tuple[
        StateWW,
        JointPlayingInformation,
        JointObservation,
        JointAction,
        InfoDict,
    ]:

        # Create roles
        list_roles = []
        for role_name, role_config_full in self.compo.items():
            role_config = deepcopy(role_config_full)
            n = role_config.pop("n")
            # if "configs" in role_config: # TODO: Implement several configurations for the same role
            assert (
                role_name in ROLES_CLASSES_WW
            ), f"Role {role_name} is not a valid role."
            if n > 0:
                for _ in range(n):
                    role = ROLES_CLASSES_WW[role_name](**role_config)
                    list_roles.append(role)
        random.shuffle(list_roles)
        assert (
            len(list_roles) == self.n_players
        ), "The number of roles must match the number of players."
        print(f"Roles : {list_roles}\n")
        # Create identities
        identities = []
        for id_player, role in enumerate(list_roles):
            identity = Identity(role, id_player)
            identities.append(identity)
        print(f"Identities : {identities}\n")
        # Set the role of player 0 as role_player_0
        if "role_player_0" in self.config and self.config["role_player_0"] is not None:
            id_role_desired = [
                i
                for i, identity in enumerate(identities)
                if identity.role.get_name() == self.config["role_player_0"]
            ][0]
            identities[0], identities[id_role_desired] = (
                identities[id_role_desired],
                identities[0],
            )
            list_roles[0], list_roles[id_role_desired] = (
                list_roles[id_role_desired],
                list_roles[0],
            )

        state = StateWW(
            n_players=self.n_players,
            list_roles=list_roles,
            identities=identities,
            compo=self.compo,
            **self.config,
        )

        # Initialize role specific variables
        print(f"Initializing roles...")
        for identity in identities:
            identity.role.initialize_role(state)

        # Perform equivalent of step_play_action to initialize the game
        state.start_new_day()

        # Get the returns of first state and extract the relevant information for reset() formalism
        (
            rewards,  # should be vec(0) at reset
            list_is_playing,
            list_obs,
            list_action_spaces,
            done,  # should be False at reset
            info,
        ) = self.step_deals_with_new_phase(state)
        return state, list_is_playing, list_obs, list_action_spaces, info

    def step(self, state: StateWW, joint_action: JointAction) -> Tuple[
        JointReward,
        StateWW,
        JointPlayingInformation,
        JointObservation,
        JointActionSpace,
        TerminalSignal,
        InfoDict,
    ]:
        # Player that played (took actions) have their observation reset here (before their actions have any effect on the state) because they are confirmed to notice the observation
        joint_action = [str_to_literal(action) for action in joint_action]
        for id_player, action in enumerate(joint_action):
            if action is not None:
                state.common_obs.reset(idx_player=id_player)

        # Play the actions of the players which influence the state of the game
        idx_begin_step = deepcopy(state.phase_manager.idx_current_phase)
        self.step_play_action(state, joint_action)
        idx_end_step = state.phase_manager.idx_current_phase

        # Check if the game is over, and if so, return the rewards
        if state.is_game_over():
            return state.step_return_victory_remaining_faction(dont_return_state=False)

        # Change the subphase index
        if idx_begin_step == idx_end_step:
            state.idx_subphase += 1
        else:
            state.idx_subphase = 0

        # Get the returns of current state and return it as well as the updated state
        (
            rewards,
            list_is_playing,
            list_obs,
            list_action_spaces,
            done,
            info,
        ) = self.step_deals_with_new_phase(state)

        return (
            rewards,
            state,
            list_is_playing,
            list_obs,
            list_action_spaces,
            done,
            info,
        )

    def step_play_action(self, state: StateWW, joint_action: JointAction) -> StateWW:
        """Perform the actions of the players in the current phase of the game.
        This will update the state of the game, and possibly change the phase.

        Args:
            state (StateWW): the current state of the game
            joint_action (JointAction): the list of actions of the players
        """
        phase = state.phase_manager.get_current_phase()
        print(
            f"Playing actions for phase {phase}.{state.idx_subphase} of turn {state.turn}..."
        )
        phase.play_action(state, joint_action)
        return

        
        

    def step_deals_with_new_phase(self, state: StateWW) -> Tuple[
        JointReward,
        JointPlayingInformation,
        JointObservation,
        JointActionSpace,
        TerminalSignal,
        InfoDict,
    ]:
        """Function called after the effect of the action on the state.

        Args:
            state (StateWW): the current state of the game

        Returns:
            JointReward: the rewards of the players
            JointPlayingInformation: the list of players playing this round.
            JointObservation: the observations of the players
            JointActionSpaces: the action spaces of the players
            TerminalSignal: a boolean indicating if the game is over
            InfoDict: a dictionary of additional information
        """
        phase = state.phase_manager.get_current_phase()

        # Check if this is a new night (in that case announce the night and initialize night variables)
        first_night_phase = state.phase_manager.get_first_night_phase()
        if first_night_phase is None:
            # No more nights, continuing the game
            state.night_attacks = defaultdict(set)
        elif first_night_phase == phase and state.idx_subphase == 0:
            # New night, announce the night and initialize night variables
            state.common_obs.add_global_message(
                f"The village is now going to sleep for night {state.turn+1}."
            )
            # Initialize night variables
            state.night_attacks = defaultdict(set)

        # # Check if this phase is related to a player that has the Pyromancer status, and in this case, skip it
        # list_ids_pyromancer = self.get_id_player_with_role(
        #     state, RolePyromancer, return_list=True
        # )
        # list_ids_target_pyromancer = self.get_id_player_with_status(
        #     state, Status.HAS_PYROMANCER_MALUS, return_list=True
        # )
        # if (
        #     len(list_ids_pyromancer) > 0
        # ):  # i.e. there is an alive Pyromancer (that already played)
        #     if (
        #         len(list_ids_target_pyromancer) > 0
        #     ):  # i.e. there is a player that has the Pyromancer malus
        #         id_player_target_pyromancer: int = list_ids_target_pyromancer[0]
        #         phases_associated_to_target_pyromancer = state.identities[
        #             id_player_target_pyromancer
        #         ].role.get_associated_phases()
        #         if (
        #             phase in phases_associated_to_target_pyromancer
        #             and not phase in RolePyromancer().get_exception_phases()
        #         ):
        #             state.common_obs.add_message(
        #                 f"The Pyromancer has unleashed their fiery power on you and burnt your house for this night. Consequently, you are unable to use your power this night.",
        #                 idx_player=id_player_target_pyromancer,
        #             )
        #             state.game_phases.advance_phase()
        #             state.identities[id_player_target_pyromancer].remove_status(
        #                 Status.HAS_PYROMANCER_MALUS
        #             )
        #             return self.step_deals_with_new_phase(state)

        return phase.return_feedback(state)

        

    def turn_angel_into_villager(self, state: StateWW):
        list_ids_angel: List[int] = self.get_id_player_with_role(
            state, RoleAngel(), return_list=True
        )
        if len(list_ids_angel) == 0:
            # Angel is already dead, return without doing anything
            return
        elif len(list_ids_angel) >= 2:
            raise ValueError("There should be at most one angel.")
        else:
            id_angel = list_ids_angel[0]
            state.identities[id_angel].change_faction(FactionsWW.VILLAGE)

    def turn_mercenary_into_villager(self, state: StateWW):
        list_ids_mercenary: List[int] = self.get_id_player_with_role(
            state, RoleMercenary(), return_list=True
        )
        if len(list_ids_mercenary) == 0:
            # Mercenary is already dead, return without doing anything
            return
        elif len(list_ids_mercenary) >= 2:
            raise ValueError("There should be at most one mercenary.")
        id_mercenary = list_ids_mercenary[0]
        # Inform the mercenary of his failure
        state.common_obs.add_message(
            f"Your target is not dead by day's 2 vote. You have failed your mission and are now a villager.",
            idx_player=id_mercenary,
        )
        # Change mercenary state to villager equivalent
        state.identities[id_mercenary].change_faction(FactionsWW.VILLAGE)
        # Remove the solo status of the mercenary
        state.identities[id_mercenary].remove_status(Status.IS_SOLO)
        # Remove the status of the mercenary target (facultative)
        list_ids_target_mercenary = self.get_id_player_with_status(
            state,
            Status.IS_MERCENARY_TARGET,
            allow_dead_player=True,
            return_list=True,
        )
        if len(list_ids_target_mercenary) == 1:
            id_target_mercenary: int = list_ids_target_mercenary[0]
            state.identities[id_target_mercenary].remove_status(
                Status.IS_MERCENARY_TARGET
            )

    def turn_player_into_wolf(self, state: StateWW, id_player: int):
        list_ids_wolves_alive = self.get_list_id_wolves_alive(state)
        state.common_obs.add_specific_message(
            f"Player {id_player} has joined the wolves.",
            list_ids_wolves_alive,
        )
        state.identities[id_player].change_faction(FactionsWW.WEREWOLVES)
        state.identities[id_player].add_status(Status.IS_WOLF)
        state.common_obs.add_message(
            f"You joined the wolves. You see the other wolves are composed of {', '.join([str(i) for i in list_ids_wolves_alive])}.",
            idx_player=id_player,
        )

    # ================= Helper functions =================

    def get_return_feedback_several_players(
        self,
        state: StateWW,
        rewards=None,
        joint_action_space: JointActionSpace = None,
    ) -> Tuple[
        JointReward,
        JointPlayingInformation,
        JointObservation,
        JointActionSpace,
        bool,
        Dict,
    ]:
        """Return the .step() returns in the case of several players play this round.

        Args:
            rewards (JointReward): the rewards of the players
            joint_action_space (JointActionSpace): the action spaces of the players

        Returns:
            Tuple[ JointReward, JointPlayingInformation, JointObservation, JointActionSpace, bool, Dict, ]: the .step() returns
        """
        # Define the list of players playing
        list_idx_players_playing = [
            i for i in range(self.n_players) if joint_action_space[i] is not None
        ]
        list_is_playing = self.empty_list_except(
            idx=list_idx_players_playing, value=True, fill=False
        )
        # Define the list of observations
        list_obs = [None] * self.n_players
        for id_player, action_space in enumerate(joint_action_space):
            if action_space is not None:
                list_obs[id_player] = state.common_obs[id_player]
        # Define rewards
        if rewards is None:
            rewards = [0.0] * self.n_players
        return (
            rewards,
            list_is_playing,
            state.common_obs,
            joint_action_space,
            False,
            {},
        )

    def get_id_player_with_role(
        self,
        state: StateWW,
        RoleClass: Type[RoleWW],
        allow_dead_player: bool = False,
        return_list: bool = False,
    ) -> int:
        """Get the ID of the player with the given role.

        Args:
            state (StateWW): the current state of the game
            role (RoleWW): the role to look for
            allow_dead_player (bool, optional): Whether to also search for the role in dead players. Defaults to True.
            return_list (bool, optional): Whether to return the list of IDs having such role, or (default behavior) the only ID having such role (this will raise an error if there is not exactly one player with the role). Defaults to False.

        Returns:
            Union[int, List[int]]: the ID of the player with the role, or the list of IDs having the role
        """
        ids_players_with_role = [
            i
            for i in range(self.n_players)
            if (allow_dead_player or state.list_are_alive[i])
            and isinstance(state.identities[i].role, RoleClass)
        ]
        if return_list:
            return ids_players_with_role
        assert (
            len(ids_players_with_role) == 1
        ), f"There should be exactly one player with the role {RoleClass}."
        id_player_with_role = ids_players_with_role[0]
        return id_player_with_role

    def get_id_player_with_status(
        self,
        state: StateWW,
        status: Status,
        allow_dead_player: bool = False,
        return_list: bool = False,
    ) -> int:
        """Get the ID of the player with the given status.

        Args:
            state (StateWW): the current state of the game
            status (Status): the status to look for
            allow_dead_player (bool, optional): Whether to also search for the status in dead players. Defaults to True.
            return_list (bool, optional): Whether to return the list of IDs having such status, or (default behavior) the only ID having such status (this will raise an error if there is not exactly one player with the status). Defaults to False.

        Returns:
            Union[int, List[int]]: the ID of the player with the status, or the list of IDs having the status
        """
        ids_players_with_status = [
            i
            for i in range(self.n_players)
            if (state.list_are_alive[i] or allow_dead_player)
            and state.identities[i].have_status(status)
        ]
        if return_list:
            return ids_players_with_status
        assert (
            len(ids_players_with_status) == 1
        ), f"There should be exactly one player with the status {status}."
        id_player_with_status = ids_players_with_status[0]
        return id_player_with_status

    

    def get_n_players(self) -> int:
        """Return the number of players in the game.

        Returns:
            int: the number of players
        """
        return self.n_players

    def render(self, state: StateWW) -> None:
        """Render the current state of the game.

        Args:
            state (State): the current state of the game
        """
        if self.config["print_common_obs"]:
            print(state.common_obs)

        if self.config["print_obs"]:
            if state.done:
                print(f"The game is over : {state.common_obs}")
            else:
                for i in range(self.n_players):
                    if list_is_playing[i]:
                        print(f"\n>>> Player {i} is playing :")
                        print(f"{state.common_obs[i]}")
                        if self.config["pause_at_each_obs_print"]:
                            input("Press any key to continue...")

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
from .statutes.base_status import Status
from .phase.base_phase import Phase
from .identity import Identity
from .roles.base_role import RoleWW
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
        compo_listing = self.initial_compo_listing
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
Composition of the game:
{compo_listing}

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
        list_roles: List[RoleWW] = []
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
        # Create identities
        identities: List[Identity] = []
        for id_player, role in enumerate(list_roles):
            identity = Identity(role, id_player)
            identities.append(identity)
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
        state.common_obs.log(f"Roles : {list_roles}\n")
        state.common_obs.log(f"Phases : {state.phase_manager}\n")
        state.common_obs.log(f"Identities : {identities}\n")

        # Get initial compo listing
        self.initial_compo_listing = state.get_compo_listing()

        # Initialize role specific variables
        for identity in identities:
            identity.role.initialize_role(state)

        # Perform equivalent of step_play_action to initialize the game
        state.start_new_day()

        # Get the returns of first state and extract the relevant information for reset() formalism
        phase = state.phase_manager.get_current_phase()
        feedback = phase.return_feedback(state)
        (
            rewards,  # should be vec(0) at reset
            list_is_playing,
            list_obs,
            list_action_spaces,
            done,  # should be False at reset
            info,
        ) = feedback
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

        feedback = None
        while feedback is None:
            
            # Check if the game is over, and if so, return the rewards
            feedback_eventual_victory = state.get_feedback_eventual_victory()
            if feedback_eventual_victory is not None:
                feedback = feedback_eventual_victory

            # Else, play the next phase
            else:
                # Change the subphase index
                if idx_begin_step == idx_end_step:
                    state.idx_subphase += 1
                else:
                    state.idx_subphase = 0

                # Get the feedback of the current phase
                phase = state.phase_manager.get_current_phase()
                feedback = phase.return_feedback(state)
                assert(feedback is None or len(feedback) == 6), f"Feedback should have 6 elements, but has {len(feedback)} elements."
                # If feedback is None, unsure the phase is advanced
                if feedback is None:
                    assert state.phase_manager.get_current_phase() != phase, f"If feedback is None, the phase should have been advanced during the return_feedback method, but it was not. Phase : {phase.get_name()}"                    
        
        # Get the returns of current state and return it as well as the updated state
        (
            rewards,
            list_is_playing,
            list_obs,
            list_action_spaces,
            done,
            info,
        ) = feedback

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
        state.common_obs.log(
            f"Playing actions for phase {phase}.{state.idx_subphase} of turn {state.turn}..."
        )
        phase.play_action(state, joint_action)
        return
      
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
            and state.identities[i].has_status(status)
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
            state.common_obs.log(state.common_obs)

        if self.config["print_obs"]:
            if state.done:
                state.common_obs.log(f"The game is over : {state.common_obs}")
            else:
                for i in range(self.n_players):
                    if list_is_playing[i]:
                        state.common_obs.log(
                            f"\n>>> Player {i} is playing :\n{state.common_obs[i]}"
                        )
                        if self.config["pause_at_each_obs_print"]:
                            input("Press any key to continue...")

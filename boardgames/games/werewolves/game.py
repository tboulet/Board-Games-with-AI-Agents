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
        context = f"""
You will play a game of Werewolves with {self.n_players} players.
  
You are playing a textual board game. Your outputs must conform to the following rules:
1. Your **reasoning** should explain your thought process in natural language.
2. Your **action** must be a valid action among those specified in the list of available actions.
   
Always separate your reasoning from your action. Your final output should explicitly label "Reasoning" and "Action," and the action must appear on a new line.
Example:
Reasoning:
"I chose this action because..."
Action:
<your action>

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
        identities = [Identity(role) for role in list_roles]
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
        idx_begin_step = deepcopy(state.game_phases.idx_current_phase)
        self.step_play_action(state, joint_action)
        idx_end_step = state.game_phases.idx_current_phase

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
        phase = state.game_phases.get_current_phase()
        print(
            f"Playing actions for phase {phase}.{state.idx_subphase} of turn {state.turn}..."
        )
        phase.play_action(state, joint_action)
        return
    
        # Day speech phase : treat the speech and check if all players have spoken
        if phase == Phase.DAY_SPEECH:

            # Treat the speech
            id_player_speaking = state.order_speech[state.idx_speech]
            assert (
                joint_action[id_player_speaking] is not None
            ), f"Player {id_player_speaking} must speak."
            state.common_obs.add_global_message(
                text=f"Player {id_player_speaking} says : {joint_action[id_player_speaking]}",
                except_idx=id_player_speaking,
            )
            state.common_obs.add_message(
                text=f"You say : {joint_action[id_player_speaking]}",
                idx_player=id_player_speaking,
            )

            # Move to the next speaker
            state.idx_speech += 1

            # Check if all players have spoken
            if state.idx_speech >= len(state.order_speech):
                # Announcing the end of the day speech
                state.common_obs.add_global_message(
                    "All players have spoken, the day is over."
                )
                # Move to the next phase
                state.game_phases.advance_phase()
                if state.turn == 0:
                    assert (
                        state.game_phases.get_current_phase() == Phase.DAY_VOTE
                    ), "Next phase should be the vote phase."
                    state.game_phases.advance_phase()  # Skip the vote phase the first day
                # Reset the speech variables for good measure
                state.order_speech = None
                state.idx_speech = None

            return state

        
            

        # Seer phase : treat the seer action
        elif phase == Phase.SEER_PHASE:
            id_seer = self.get_id_player_with_role(state, RoleSeer())
            id_target_seer: int = joint_action[id_seer]
            assert id_target_seer in range(
                self.n_players
            ), f"Player {id_seer} must choose a valid player to investigate, but chose {id_target_seer}."
            assert state.list_are_alive[
                id_target_seer
            ], f"Player {id_seer} cannot investigate a dead player, but chose {id_target_seer}."
            role_target_seer = state.identities[id_target_seer].role
            state.common_obs.add_message(
                f"You have investigated player {id_target_seer}. You see their role is {role_target_seer}.",
                idx_player=id_seer,
            )
            # Advance to the next phase
            state.game_phases.advance_phase()
            return state

        # Witch phase : treat the witch action
        elif phase == Phase.WITCH_PHASE:
            id_witch = self.get_id_player_with_role(state, RoleWitch())
            action_witch: str = joint_action[id_witch]
            if action_witch == "Do nothing":
                state.common_obs.add_message(
                    "You have decided to not use any potion for now. ",
                    idx_player=id_witch,
                )
            elif action_witch == "Save":
                assert state.night_attacks, "No player to save."
                state.identities[id_witch].remove_status(Status.HAS_HEALING_POTION)
                id_player_victim = self.get_ids_wolf_victims(state)[0]
                for cause_of_death_wolf in [
                    CAUSES_OF_DEATH.WOLF_ATTACK,
                    CAUSES_OF_DEATH.PERFIDIOUS_WOLF_ADDITIONAL_ATTACK,
                ]:
                    state.night_attacks[id_player_victim].remove(cause_of_death_wolf)
                state.common_obs.add_message(
                    f"You have saved player {id_player_victim}.",
                    idx_player=id_witch,
                )
            elif action_witch.startswith("Kill"):
                state.identities[id_witch].remove_status(Status.HAS_DEATH_POTION)
                id_target_witch = int(action_witch.split(" ")[1])
                state.night_attacks[id_target_witch].add(
                    CAUSES_OF_DEATH.WITCH_DEATH_POTION
                )
                state.common_obs.add_message(
                    f"You have eliminated player {id_target_witch}.",
                    idx_player=id_witch,
                )
            else:
                raise ValueError(f"Invalid action for the witch : {action_witch}.")
            # Advance to the next phase
            state.game_phases.advance_phase()
            # If the witch has used both potions, remove the witch phase from the game phases
            if (
                not state.identities[id_witch].have_status(Status.HAS_HEALING_POTION)
            ) and (not state.identities[id_witch].have_status(Status.HAS_DEATH_POTION)):
                state.game_phases.remove_phase(Phase.WITCH_PHASE)
            return state

        # Savior phase : treat the savior action
        elif phase == Phase.SAVIOR_PHASE:
            id_savior = self.get_id_player_with_role(state, RoleSavior())
            id_target_savior: int = joint_action[id_savior]
            state.identities[id_target_savior].add_status(Status.IS_PROTECTED_SAVIOR)
            state.common_obs.add_message(
                f"You have protected player {id_target_savior}.",
                idx_player=id_savior,
            )
            # Advance to the next phase
            state.game_phases.advance_phase()
            return state

        # Infection phase : infect a player (change its wolf status, and inform them and the wolf of the infection)
        elif phase == Phase.INFECTION_PHASE:
            # Check whether the black wolf infected the wolf's victim
            id_black_wolf = self.get_id_player_with_role(state, RoleBlackWolf())
            if joint_action[id_black_wolf] == "Do nothing":
                state.game_phases.advance_phase()
                return state
            else:
                assert state.identities[id_black_wolf].have_status(
                    Status.HAS_INFECTION_POWER
                ), "The Black Wolf does not have the infection power."
                id_player_victim = self.get_ids_wolf_victims(state)[0]
                # Infect the player
                state.identities[id_player_victim].add_status(Status.IS_WOLF)
                state.identities[id_player_victim].change_faction(FactionsWW.WEREWOLVES)
                # Inform the player and the wolves of the infection
                list_id_wolves_alive = self.get_list_id_wolves_alive(state)
                state.common_obs.add_message(
                    f"You have been infected by the Black Wolf. You are now a werewolf and must win with the werewolves faction. You conserve any previous power you had.",
                    idx_player=id_player_victim,
                )
                self.turn_player_into_wolf(state, id_player_victim)
                # Advance to the next phase
                state.game_phases.advance_phase()
                # Remove the infection phase from the game phases
                state.game_phases.remove_phase(Phase.INFECTION_PHASE)
                state.identities[id_black_wolf].remove_status(
                    Status.HAS_INFECTION_POWER
                )
                return state

        # Hunter phase : treat the hunter action
        elif phase == Phase.HUNTER_CHOICE:
            id_hunter = self.get_id_player_with_role(
                state, RoleHunter(), allow_dead_player=True
            )
            id_target_hunter: int = joint_action[id_hunter]
            state.common_obs.add_message(
                f"You have eliminated player {id_target_hunter}.",
                idx_player=id_hunter,
            )
            state.common_obs.add_global_message(
                f"The Hunter has decided to eliminate player {id_target_hunter}."
            )
            self.apply_death_consequences(
                state, id_target_hunter, CAUSES_OF_DEATH.HUNTER_SHOT
            )
            # Advance to the next phase
            state.game_phases.advance_phase()
            # Self destruct the phase
            state.game_phases.remove_phase(Phase.HUNTER_CHOICE)
            return state

        # Gravedigger phase : treat the gravedigger action
        elif phase == Phase.GRAVEDIGGER_CHOICE:
            id_gravedigger = self.get_id_player_with_role(
                state, RoleGravedigger(), allow_dead_player=True
            )
            id_target_gravedigger: int = joint_action[id_gravedigger]
            state.common_obs.add_message(
                f"You have decided to dig the grave of player {id_target_gravedigger}.",
                idx_player=id_gravedigger,
            )
            # Randomly select another player of the opposite faction to reveal
            if state.identities[id_target_gravedigger].faction == FactionsWW.VILLAGE:
                list_candidates = [
                    i
                    for i in range(self.n_players)
                    if state.identities[i].faction != FactionsWW.VILLAGE
                ]
            else:
                list_candidates = [
                    i
                    for i in range(self.n_players)
                    if state.identities[i].faction == FactionsWW.VILLAGE
                ]
            id_other = random.choice(list_candidates)
            state.common_obs.add_global_message(
                f"The Gravedigger has decided to dig the grave of player {id_target_gravedigger} and player {id_other}. "
                f"One of them is a villager, the other one is not, but you do not know which one is which."
            )
            # Advance to the next phase
            state.game_phases.advance_phase()
            # Self destruct the phase
            state.game_phases.remove_phase(Phase.GRAVEDIGGER_CHOICE)
            return state

        # White Wolf phase : treat the white wolf action
        elif phase == Phase.WHITE_WOLF_ATTACK:
            id_white_wolf = self.get_id_player_with_role(state, RoleWhiteWolf())
            id_target_white_wolf: int = joint_action[id_white_wolf]
            state.common_obs.add_message(
                f"You have attacked player {id_target_white_wolf}.",
                idx_player=id_white_wolf,
            )
            state.night_attacks[id_target_white_wolf].add(
                CAUSES_OF_DEATH.WHITE_WOLF_ATTACK
            )
            # Advance to the next phase
            state.game_phases.advance_phase()
            return state

        # Necromancer phase : treat the necromancer/dead action
        elif phase == Phase.NECROMANCER_PHASE:
            id_necromancer = self.get_id_player_with_role(state, RoleNecromancer())
            if state.necromancer_dict["sub-phase"] == "pick":
                # Save the target player to speak with and advance to the ask sub-phase
                id_target_necromancer: int = joint_action[id_necromancer]
                state.common_obs.add_message(
                    f"You have decided to speak with player {id_target_necromancer}.",
                    idx_player=id_necromancer,
                )
                state.necromancer_dict["player_picked"] = id_target_necromancer
                state.necromancer_dict["sub-phase"] = "ask"
                return state
            elif state.necromancer_dict["sub-phase"] == "ask":
                # Save the question and advance to the answer sub-phase
                id_target_necromancer = int(state.necromancer_dict["player_picked"])
                question_necromancer: str = joint_action[id_necromancer]
                state.common_obs.add_message(
                    f"Your question to player {id_target_necromancer} was transmitted.",
                    idx_player=id_necromancer,
                )
                state.necromancer_dict["question"] = question_necromancer
                state.necromancer_dict["sub-phase"] = "answer"
                return state
            elif state.necromancer_dict["sub-phase"] == "answer":
                # Send back the answer to the necromancer
                id_target_necromancer = int(state.necromancer_dict["player_picked"])
                answer_from_dead: str = joint_action[id_target_necromancer]
                state.common_obs.add_message(
                    f"Player {id_target_necromancer} answered : {answer_from_dead}.",
                    idx_player=id_necromancer,
                )
                state.necromancer_dict = (
                    {}
                )  # Reset the necromancer dict for good measure
                # Advance to the next phase
                state.game_phases.advance_phase()
                return state

        # Thief phase : if thief has the steal power, mark the target and remove thief power
        elif phase == Phase.THIEF_PHASE:
            id_thief = self.get_id_player_with_role(state, RoleThief())
            action_thief: str = joint_action[id_thief]
            if action_thief == "Do nothing":
                state.common_obs.add_message(
                    "You have decided to not steal any role for now. ",
                    idx_player=id_thief,
                )
                state.game_phases.advance_phase()
                return state
            else:
                id_target_thief = int(action_thief)
                # Mark the target as the thief target
                state.identities[id_target_thief].add_status(Status.IS_THIEF_TARGET)
                # Remove the thief power
                state.identities[id_thief].remove_status(Status.HAS_THIEF_POWER)
                # Inform the thief he used his power
                state.common_obs.add_message(
                    f"You have used your power on player {id_target_thief}. When they die, you will acquire their role starting from the next night.",
                    idx_player=id_thief,
                )
                # Advance to the next phase
                state.game_phases.advance_phase()
                return state

        # Crow phase : inflict the crow curse on a player
        elif phase == Phase.CROW_PHASE:
            id_crow = self.get_id_player_with_role(state, RoleCrow())
            action_crow: str = joint_action[id_crow]
            if action_crow == "Do nothing":
                state.common_obs.add_message(
                    "You have decided to not curse any player",
                    idx_player=id_crow,
                )
            else:
                id_target_crow = int(action_crow)
                state.common_obs.add_message(
                    f"You have decided to curse player {id_target_crow}.",
                    idx_player=id_crow,
                )
                state.common_obs.add_global_message(
                    (
                        f"The Crow has decided to curse player {id_target_crow}. "
                        "This player will receive 2 additional votes against them during the next day."
                    )
                )
                state.identities[id_target_crow].add_status(Status.HAS_CROW_MALUS)
            # Advance to the next phase
            state.game_phases.advance_phase()
            return state

        # Invisible phase : check the invisible attacks
        elif phase == Phase.INVISIBLE_PHASE:
            list_ids_invisible: List[int] = self.get_id_player_with_status(
                state, status=Status.IS_INVISIBLE, return_list=True
            )
            assert (
                len(list_ids_invisible) >= 2
            ), "There should be at least 2 invisible players if this phase is played."
            assert all(
                [
                    isinstance(state.identities[i].role, RoleInvisible)
                    for i in list_ids_invisible
                ]
            ), "All invisible players should have the invisible role."
            for id_invi in list_ids_invisible:
                action_invi = joint_action[id_invi]
                assert (
                    action_invi is not None
                ), f"Player {id_invi} should have chosen an action."
                if action_invi == "Do nothing":
                    state.common_obs.add_message(
                        "You have decided to not attack anyone.",
                        idx_player=id_invi,
                    )
                else:
                    id_target_invi = int(action_invi)
                    role_target_invi = state.identities[id_target_invi].role
                    role_invi: RoleInvisible = state.identities[id_invi].role
                    state.common_obs.add_message(
                        f"You have decided to attack player {id_target_invi}.",
                        idx_player=id_invi,
                    )
                    # Player id_invi attacks player id_target_invi. Check if the target is an invisible player
                    if id_target_invi in list_ids_invisible:
                        assert isinstance(
                            role_target_invi, RoleInvisible
                        ), f"Player {id_target_invi} is not an invisible player."
                        state.night_attacks[id_target_invi].add(
                            role_invi.get_associated_cause_of_death()
                        )
                        state.common_obs.add_message(
                            f"Your correctly guessed that player {id_target_invi} was invisible, your attack was sent to them.",
                            idx_player=id_invi,
                        )
                    else:
                        assert not isinstance(
                            role_target_invi, RoleInvisible
                        ), f"Player {id_target_invi} is an invisible player."
                        state.night_attacks[id_invi].add(
                            CAUSES_OF_DEATH.FAILED_INVISIBLE_ATTACK
                        )
                        state.common_obs.add_message(
                            f"Your uncorrectly guessed that player {id_target_invi} was invisible, your attack was sent to yourself.",
                            idx_player=id_invi,
                        )

            # Advance to the next phase
            state.game_phases.advance_phase()
            return state

        # Perfidious Wolf Attack phase : treat the perfidious wolf attack
        elif phase == Phase.PERFIDIOUS_WOLF_ATTACK:
            id_perf_wolf = self.get_id_player_with_role(state, RolePerfidiousWolf())
            id_target_perf_wolf = int(joint_action[id_perf_wolf])
            state.common_obs.add_message(
                f"You have attacked player {id_target_perf_wolf}.",
                idx_player=id_perf_wolf,
            )
            state.night_attacks[id_target_perf_wolf].add(
                CAUSES_OF_DEATH.PERFIDIOUS_WOLF_ADDITIONAL_ATTACK
            )
            # Advance to the next phase
            state.game_phases.advance_phase()
            return state

        # Pyromancer phase : treat the pyromancer action
        elif phase == Phase.PYROMANCER_PHASE:
            id_pyromancer = self.get_id_player_with_role(state, RolePyromancer())
            action_pyromancer: str = joint_action[id_pyromancer]
            if action_pyromancer == "Do nothing":
                state.common_obs.add_message(
                    "You have decided to not use your power for now.",
                    idx_player=id_pyromancer,
                )
            else:
                id_target_pyromancer = int(action_pyromancer)
                state.common_obs.add_message(
                    f"You have decided to burn the house of player {id_target_pyromancer}.",
                    idx_player=id_pyromancer,
                )
                state.identities[id_target_pyromancer].add_status(
                    Status.HAS_PYROMANCER_MALUS
                )
            # Advance to the next phase
            state.game_phases.advance_phase()
            return state

        # Wolfdog Choice phase : treat the choice of the wolfdog
        elif phase == Phase.WOLFDOG_CHOICE:
            id_wolfdog = self.get_id_player_with_role(state, RoleWolfdog())
            action_wolfdog: str = joint_action[id_wolfdog]
            if action_wolfdog == "Join villagers":
                state.common_obs.add_message(
                    "You have decided to join the villagers. You must now win with the village faction.",
                    idx_player=id_wolfdog,
                )
            else:
                state.common_obs.add_message(
                    "You have decided to join the wolves. You must now win with the werewolves faction.",
                    idx_player=id_wolfdog,
                )
                self.turn_player_into_wolf(state, id_wolfdog)
            # Advance to the next phase
            state.game_phases.advance_phase()
            # Remove the wolfdog phase from the game phases
            state.game_phases.remove_phase(Phase.WOLFDOG_CHOICE)
            return state

        # Judge phase : if judge use its power, inform the village and set the phase to Day Speech
        elif phase == Phase.JUDGE_PHASE:
            id_judge = self.get_id_player_with_role(state, RoleJudge())
            action_judge: str = joint_action[id_judge]
            if action_judge == "Do nothing":
                state.common_obs.add_message(
                    "You have decided to not use your power for now.",
                    idx_player=id_judge,
                )
                state.game_phases.advance_phase()
                return state
            elif action_judge == "Create vote":
                state.common_obs.add_global_message(
                    "The Judge has decided to create a 2nd vote for today. The day speech will now begin."
                )
                # Set the phase to Day Speech and mark the night_attacks as absence of night attacks due to judge power
                state.game_phases.set_current_phase(Phase.DAY_SPEECH)
                state.turn -= 1  # The day speech phase will increment the turn so we need to decrement it here
                state.night_attacks = RoleJudge().get_absent_night_indicator()
                # Remove Judge power and Judge phase
                state.identities[id_judge].remove_status(Status.HAS_JUDGE_POWER)
                state.game_phases.remove_phase(Phase.JUDGE_PHASE)
                return state
            else:
                raise ValueError(f"Invalid action for the Judge : {action_judge}.")

        # Fox phase : treat the fox action
        elif phase == Phase.FOX_PHASE:
            id_fox = self.get_id_player_with_role(state, RoleFox())
            action_fox = joint_action[id_fox]
            # Treat string action (from textual agents)
            if isinstance(action_fox, str):  # untested
                action_fox = action_fox.split(" ")
            # Check if the action is valid
            assert isinstance(action_fox, list), "Action must be a list."
            # Perform the smell action
            do_smelled_players_contain_wolves = False
            for id_target_fox in action_fox:
                id_target_fox = int(id_target_fox)
                if state.identities[id_target_fox].have_status(Status.IS_WOLF):
                    do_smelled_players_contain_wolves = True
            # Inform the fox of the result
            if do_smelled_players_contain_wolves:
                state.common_obs.add_message(
                    "You have smelled the presence of at least one wolf among the players you have chosen.",
                    idx_player=id_fox,
                )
            else:
                state.common_obs.add_message(
                    "You have smelled the absence of wolves among the players you have chosen. You now know that none of them are wolves in exchange of losing your power. ",
                    idx_player=id_fox,
                )
                # Remove the phase from the game phases
                state.game_phases.advance_phase()
                state.game_phases.remove_phase(Phase.FOX_PHASE)
            return state

        # Sister speech phase : treat the sister speech
        elif phase == Phase.SISTER_SPEECH:
            try:
                id_sister_1, id_sister_2 = self.get_id_player_with_role(
                    state, RoleSister(), return_list=True
                )
            except ValueError:
                raise ValueError(
                    "There should be exactly 2 sisters if this phase is played."
                )
            state.common_obs.add_specific_message(
                f"You sent your message to your sister.",
                list_idx_player=[id_sister_1, id_sister_2],
            )
            action_sister_1 = joint_action[id_sister_1]
            action_sister_2 = joint_action[id_sister_2]
            state.common_obs.add_message(
                f"You received the message from your sister : {action_sister_2}.",
                idx_player=id_sister_1,
            )
            state.common_obs.add_message(
                f"You received the message from your sister : {action_sister_1}.",
                idx_player=id_sister_2,
            )
            # Advance to the next phase
            state.game_phases.advance_phase()
            return state

        else:
            raise NotImplementedError(f"Phase {phase} not implemented yet.")

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
        phase = state.game_phases.get_current_phase()

        # Check if this is a new night (in that case announce the night and initialize night variables)
        first_night_phase = state.game_phases.get_first_night_phase()
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
        
        # Seer phase : Ask the seer to choose a player to investigate
        if phase == Phase.SEER_PHASE:
            id_seer = self.get_id_player_with_role(state, RoleSeer())
            list_id_players_protected_candidates = [
                str(i) for i in range(self.n_players) if state.list_are_alive[i]
            ]
            state.common_obs.add_message(
                f"Seer, you can now choose a player to investigate among the alive players : {list_id_players_protected_candidates}.",
                idx_player=id_seer,
            )
            action_space = FiniteActionSpace(
                actions=list_id_players_protected_candidates
            )
            return self.get_return_feedback_one_player(
                state=state, id_player=id_seer, action_space=action_space
            )

        # Witch phase : get the wolf victim, and the player to eventually kill
        elif phase == Phase.WITCH_PHASE:
            # Inform the witch its turn is starting
            id_witch = self.get_id_player_with_role(state, RoleWitch())
            state.common_obs.add_message(
                (
                    f"Witch, you can now use one of your potions if you have any. "
                    f"You can also choose to do nothing and keep your potions for later use with action 'Do nothing'. "
                ),
                idx_player=id_witch,
            )
            list_actions = ["Do nothing"]
            # Get the wolf victim and inform the witch of it
            ids_wolf_victims = self.get_ids_wolf_victims(state)
            assert (
                len(ids_wolf_victims) <= 1
            ), "There should be at most one wolf victim. (Not implemented yet)"
            if len(ids_wolf_victims) == 1:
                id_wolf_victim = ids_wolf_victims[0]
                state.common_obs.add_message(
                    f"You see the victim of the wolves is player {id_wolf_victim}. You can choose to save them by consuming your healing potion with action 'Save'.",
                    idx_player=id_witch,
                )
            else:
                state.common_obs.add_message(
                    f"You see there is no victim of the wolves this night.",
                    idx_player=id_witch,
                )
            # Propose the witch to save the wolf victim (if any, and if the witch has the healing potion)
            if (
                state.identities[id_witch].have_status(Status.HAS_HEALING_POTION)
                and len(ids_wolf_victims) >= 1
            ):
                list_actions.append("Save")
            # Propose the witch to choose a player to kill (if the witch has the death potion)
            if state.identities[id_witch].have_status(Status.HAS_DEATH_POTION):
                list_actions_kill = []
                for i in range(self.n_players):
                    if (
                        state.list_are_alive[i]
                        and (i != id_witch)
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
                        idx_player=id_witch,
                    )
            # Return feedback to the witch
            action_space = FiniteActionSpace(actions=list_actions)
            return self.get_return_feedback_one_player(
                state=state, id_player=id_witch, action_space=action_space
            )

        # Savior phase : ask the savior which player to protect
        elif phase == Phase.SAVIOR_PHASE:
            id_savior = self.get_id_player_with_role(state, RoleSavior())
            # Get the list of players the savior can protect, and remove the previous protected player from the list
            list_id_players_protected_candidates = [
                str(i) for i in range(self.n_players) if state.list_are_alive[i]
            ]
            id_previous_protected = self.get_id_player_with_status(
                state, Status.IS_PROTECTED_SAVIOR
            )
            list_id_players_protected_candidates.remove(str(id_previous_protected))
            # Remove the previous protected player from the protected status
            state.identities[id_previous_protected].remove_status(
                Status.IS_PROTECTED_SAVIOR
            )
            # Inform the savior of the players they can protect
            state.common_obs.add_message(
                f"Savior, you can now choose a player to protect among the alive players : {list_id_players_protected_candidates}. You can't protect the same player as the previous night.",
                idx_player=id_savior,
            )
            action_space = FiniteActionSpace(
                actions=list_id_players_protected_candidates
            )
            return self.get_return_feedback_one_player(
                state=state, id_player=id_savior, action_space=action_space
            )

        # Infection phase : ask the infected player to choose whether to infect the attacked player
        elif phase == Phase.INFECTION_PHASE:
            ids_wolf_victims = self.get_ids_wolf_victims(state)
            if len(ids_wolf_victims) == 0:
                # No wolf victim, no infection, skip the phase
                state.game_phases.advance_phase()
                return self.step_deals_with_new_phase(state)

            else:
                # Ask the black wolf to choose whether to infect the attacked player
                id_wolf_victim = ids_wolf_victims[0]
                id_black_wolf = self.get_id_player_with_role(state, RoleBlackWolf())
                assert state.identities[id_black_wolf].have_status(
                    Status.HAS_INFECTION_POWER
                ), "The Black Wolf does not have the infection power."
                state.common_obs.add_message(
                    (
                        f"Black Wolf, you can now choose to infect the player attacked by the wolves, player {id_wolf_victim}, "
                        "if you do so, it will consume your infection power and turn the player into a wolf. "
                    ),
                    idx_player=id_black_wolf,
                )
                action_space = FiniteActionSpace(actions=["Infect", "Do nothing"])
                return self.get_return_feedback_one_player(
                    state=state, id_player=id_black_wolf, action_space=action_space
                )

        # Hunter choice phase : ask the hunter which player to kill.
        # This phase will self-destruct as it is not removed by by the apply_death_consequences method (because hunter is already dead)
        elif phase == Phase.HUNTER_CHOICE:
            id_hunter = self.get_id_player_with_role(
                state, RoleHunter(), allow_dead_player=True
            )
            list_id_players_target_candidate = [
                str(i) for i in range(self.n_players) if state.list_are_alive[i]
            ]
            state.common_obs.add_message(
                f"Hunter, you are dead, but can shot a final bullet before leaving the village. Choose a player to kill among the alive players : {list_id_players_target_candidate}.",
                idx_player=id_hunter,
            )
            action_space = FiniteActionSpace(actions=list_id_players_target_candidate)
            return self.get_return_feedback_one_player(
                state=state, id_player=id_hunter, action_space=action_space
            )

        # Gravedigger choice phase : ask the gravedigger which player to dig a grave
        elif phase == Phase.GRAVEDIGGER_CHOICE:
            id_gravedigger = self.get_id_player_with_role(
                state, RoleGravedigger(), allow_dead_player=True
            )
            list_id_players_gravable = [
                str(i)
                for i in range(self.n_players)
                if (state.list_are_alive[i] and i != id_gravedigger)
            ]
            state.common_obs.add_message(
                (
                    f"Gravedigger, you can now choose a player to dig the grave among the dead players : {list_id_players_gravable}. "
                    f"This will reveal publicly the name of this player and another player of the opposite faction.",
                ),
                idx_player=id_gravedigger,
            )
            action_space = FiniteActionSpace(actions=list_id_players_gravable)
            return self.get_return_feedback_one_player(
                state=state, id_player=id_gravedigger, action_space=action_space
            )

        # White wolf attack phase : ask the white wolf which player to attack
        elif phase == Phase.WHITE_WOLF_ATTACK:
            # Skip the phase on even turns
            if state.turn % 2 == 0:
                state.game_phases.advance_phase()
                return self.step_deals_with_new_phase(state)
            else:
                id_white_wolf = self.get_id_player_with_role(state, RoleWhiteWolf())
                list_id_players_target_candidate = [
                    str(i)
                    for i in range(self.n_players)
                    if (state.list_are_alive[i] and i != id_white_wolf)
                ]
                state.common_obs.add_message(
                    f"White Wolf, you can now choose a player to attack among the alive players : {list_id_players_target_candidate}.",
                    idx_player=id_white_wolf,
                )
                action_space = FiniteActionSpace(
                    actions=list_id_players_target_candidate
                )
                return self.get_return_feedback_one_player(
                    state=state, id_player=id_white_wolf, action_space=action_space
                )

        # Mercenary phase : remove mercenary_target status on turn 2 then self-destruct the phase
        elif phase == Phase.MERCENARY_CHECK:
            # Skip the phase on turn 0
            if state.turn <= 0:
                state.game_phases.advance_phase()
                return self.step_deals_with_new_phase(state)
            # Check if the mercenary's target is dead
            elif state.turn == 1:
                state.game_phases.advance_phase()
                state.game_phases.remove_phase(Phase.MERCENARY_CHECK)
                self.turn_mercenary_into_villager(state)
                return self.step_deals_with_new_phase(state)
            else:
                raise ValueError(
                    f"Phase {phase} should not be played on turn {state.turn}."
                )

        # Necromancer phase : ask the necromancer which player to speak with and what to ask to them
        elif phase == Phase.NECROMANCER_PHASE:
            id_necromancer = self.get_id_player_with_role(state, RoleNecromancer())
            list_id_players_dead = [
                str(i) for i in range(self.n_players) if (not state.list_are_alive[i])
            ]

            # Skip the phase if there is no dead player
            if len(list_id_players_dead) == 0:
                state.common_obs.add_message(
                    "Necromancer, you can't use your power as there is no dead player to speak with.",
                    idx_player=id_necromancer,
                )
                state.game_phases.advance_phase()
                return self.step_deals_with_new_phase(state)

            # If sub-phase is "pick", ask the Necromancer to choose a dead player to speak with
            if "sub-phase" not in state.necromancer_dict:
                state.necromancer_dict["sub-phase"] = "pick"
                state.common_obs.add_message(
                    f"Necromancer, you can now choose a dead player to speak with among the dead players : {list_id_players_dead}.",
                    idx_player=id_necromancer,
                )
                action_space = FiniteActionSpace(actions=list_id_players_dead)
                return self.get_return_feedback_one_player(
                    state=state, id_player=id_necromancer, action_space=action_space
                )

            # If sub-phase is "ask", ask the Necromancer to ask a question to the dead player they have chosen
            elif state.necromancer_dict.get("sub-phase") == "ask":
                state.common_obs.add_message(
                    f"Necromancer, you can now ask a question to the dead player you have chosen to speak with (player {state.necromancer_dict['player_picked']}).",
                    idx_player=id_necromancer,
                )
                action_space = TextualActionSpace(
                    description=f"Ask a question to the dead player you have chosen to speak with (player {state.necromancer_dict['player_picked']})."
                )
                return self.get_return_feedback_one_player(
                    state=state, id_player=id_necromancer, action_space=action_space
                )

            # If sub-phase is "answer", ask the dead player to answer the Necromancer's question
            elif state.necromancer_dict.get("sub-phase") == "answer":
                id_dead_picked = int(state.necromancer_dict["player_picked"])
                state.common_obs.add_message(
                    f"With its power, the Necromancer has decided to communicate with you beyond the grave. You can now answer their question.",
                    idx_player=id_dead_picked,
                )
                action_space = TextualActionSpace(
                    description=f"Answer the Necromancer's question."
                )
                return self.get_return_feedback_one_player(
                    state=state, id_player=id_dead_picked, action_space=action_space
                )

            else:
                raise ValueError(
                    f"Invalid sub-phase for the Necromancer : {state.necromancer_dict.get('sub-phase')}."
                )

        # Thief phase :
        elif phase == Phase.THIEF_PHASE:
            id_thief = self.get_id_player_with_role(state, RoleThief())
            if state.identities[id_thief].have_status(Status.HAS_THIEF_POWER):
                # If thief still has the steal power, propose the thief to choose a player to inherit the role from if they dies
                list_player_target_candidate = [
                    str(i)
                    for i in range(self.n_players)
                    if state.list_are_alive[i] and i != id_thief
                ]
                state.common_obs.add_message(
                    f"Thief, you can now choose to use you power to inherit its power if he dies. You can only do this once per game. If you wish to wait, you can play the action 'Do nothing'.",
                    idx_player=id_thief,
                )
                action_space = FiniteActionSpace(
                    actions=["Do nothing"] + list_player_target_candidate
                )
                return self.get_return_feedback_one_player(
                    state=state, id_player=id_thief, action_space=action_space
                )
            elif not state.identities[id_thief].have_status(Status.HAS_STOLEN_ROLE):
                # If thief has not the steal power but have not stolen yet, check if marked player is dead and steal the role if so, then go to the next phase
                id_thief_target = self.get_id_player_with_status(
                    state, Status.IS_THIEF_TARGET, allow_dead_player=True
                )
                if not state.list_are_alive[id_thief_target]:
                    # If the thief target is dead, perform the role stealing
                    # Steal the role
                    role_stolen = state.identities[id_thief_target].role
                    state.identities[id_thief].role = role_stolen
                    # Change the faction
                    state.identities[id_thief].change_faction(
                        faction=role_stolen.get_initial_faction()
                    )
                    # Change the status and add the initial status of the role
                    state.identities[id_thief].remove_status(
                        Status.IS_SOLO
                    )  # Thief is not solo anymore (but can regain it with the new role)
                    state.identities[id_thief].add_status(Status.HAS_STOLEN_ROLE)
                    state.identities[id_thief].statutes.extend(
                        role_stolen.get_initial_statutes()
                    )
                    state.identities[id_thief].statutes = list(
                        set(state.identities[id_thief].statutes)
                    )  # Remove duplicates
                    # Inform the thief of their new role
                    state.common_obs.add_message(
                        f"You have acquired the role of player {id_thief_target} : {role_stolen} in its current state.",
                        idx_player=id_thief,
                    )
                # Advance to the next phase
                state.game_phases.advance_phase()
                return self.step_deals_with_new_phase(state)
            else:
                # If thief has already stolen a role, skip the phase
                state.game_phases.advance_phase()
                return self.step_deals_with_new_phase(state)

        # Crow phase : ask the crow to choose a player to designate for its malus
        elif phase == Phase.CROW_PHASE:
            id_crow = self.get_id_player_with_role(state, RoleCrow())
            list_id_players_target_candidate = [
                str(i)
                for i in range(self.n_players)
                if state.list_are_alive[i] and i != id_crow
            ]
            state.common_obs.add_message(
                f"Crow, you can now choose a player to designate among {list_id_players_target_candidate}. They will receive 2 additional votes against them during the next day. You can also choose to do nothing with the action 'Do nothing'.",
                idx_player=id_crow,
            )
            action_space = FiniteActionSpace(
                actions=list_id_players_target_candidate + ["Do nothing"]
            )
            return self.get_return_feedback_one_player(
                state=state, id_player=id_crow, action_space=action_space
            )

        # Invisible phase : propose the invisible attack
        elif phase == Phase.INVISIBLE_PHASE:
            list_ids_invisible: List[int] = self.get_id_player_with_status(
                state, status=Status.IS_INVISIBLE, return_list=True
            )

            # If there are 0 or 1 invisible player, skip the phase
            if len(list_ids_invisible) <= 1:
                state.game_phases.advance_phase()
                return self.step_deals_with_new_phase(state)

            # Else, propose the invisible attack to each invisible player
            random.shuffle(list_ids_invisible)
            joint_action_space = [None] * self.n_players
            for id_invi in list_ids_invisible:
                role_invi = state.identities[id_invi].role
                list_id_target_of_invisible_attack = [
                    i
                    for i in range(self.n_players)
                    if state.list_are_alive[i] and i != id_invi
                ]
                state.common_obs.add_message(
                    (
                        f"{role_invi.get_name()}, you are given the opportunity to perform an 'invisible attack' on another player. "
                        "Please not that if you pick a player that is not invisible, the attack will fail and you will die instead. "
                        "You must therefore be absolutely sure of your choice. "
                        "If you wish to not perform the attack, you can play the action 'Do nothing'."
                        f"The invisible roles currently alive, except you, are : {[state.identities[i].role.get_name() for i in list_id_target_of_invisible_attack]}."
                    ),
                    idx_player=id_invi,
                )
                joint_action_space[id_invi] = FiniteActionSpace(
                    actions=[str(i) for i in list_id_target_of_invisible_attack]
                    + ["Do nothing"]
                )
            return self.get_return_feedback_several_players(
                state=state, joint_action_space=joint_action_space
            )

        # Perfidious Wolf Attack phase : if the wolf has the power, he can kill another player this night
        elif phase == Phase.PERFIDIOUS_WOLF_ATTACK:
            id_perfidious_wolf = self.get_id_player_with_role(
                state, RolePerfidiousWolf()
            )
            if not state.identities[id_perfidious_wolf].have_status(
                Status.HAS_PERFIDIOUS_POWER
            ):
                # Skip the phase if the wolf does not have the power
                state.game_phases.advance_phase()
                return self.step_deals_with_new_phase(state)
            else:
                list_id_players_target_candidate = [
                    str(i)
                    for i in range(self.n_players)
                    if state.list_are_alive[i] and i != id_perfidious_wolf
                ]
                state.common_obs.add_message(
                    f"Perfidious Wolf, you can now choose a player to attack among the alive players : {list_id_players_target_candidate}.",
                    idx_player=id_perfidious_wolf,
                )
                action_space = FiniteActionSpace(
                    actions=list_id_players_target_candidate
                )
                return self.get_return_feedback_one_player(
                    state=state, id_player=id_perfidious_wolf, action_space=action_space
                )

        # Victory check phase : check win conditions for certain roles
        elif phase == Phase.VICTORY_CHECK:
            list_ids_players_alive = [
                i for i in range(self.n_players) if state.list_are_alive[i]
            ]
            identities_alive = {i: state.identities[i] for i in list_ids_players_alive}
            winning_factions = []
            for i, identity in identities_alive.items():
                # Unsure the current player faction is the same as the faction of its role
                if identity.role.is_win_condition_achieved and (
                    identity.faction == identity.role.get_initial_faction()
                ):
                    winning_factions.append(identity.role.get_initial_faction())
            if len(winning_factions) == 0:
                # No player has won yet, go to next phase
                state.game_phases.advance_phase()
                return self.step_deals_with_new_phase(state)
            elif len(winning_factions) == 1:
                # One faction has won, return the victory
                return self.step_return_victory_of_faction(state, winning_factions[0])
            else:
                # Multiple factions have won, they each get +1 reward.
                state.common_obs.add_global_message(
                    f"Multiple factions have won the game together : {', '.join(winning_factions)}."
                )
                return self.step_return_victory_of_faction(state, winning_factions)

        # Pyromancer phase : ask the pyromancer to choose a player to burn
        elif phase == Phase.PYROMANCER_PHASE:
            id_pyromancer = self.get_id_player_with_role(state, RolePyromancer())
            list_id_players_target_candidate = [
                str(i)
                for i in range(self.n_players)
                if state.list_are_alive[i] and i != id_pyromancer
            ]
            state.common_obs.add_message(
                f"Pyromancer, you can now choose a player to burn among the alive players : {list_id_players_target_candidate}. This will prevent them to use their power this night. If you wish to do nothing, you can play the action 'Do nothing'.",
                idx_player=id_pyromancer,
            )
            action_space = FiniteActionSpace(
                actions=list_id_players_target_candidate + ["Do nothing"]
            )
            return self.get_return_feedback_one_player(
                state=state, id_player=id_pyromancer, action_space=action_space
            )

        # Angel Check Phase : if this phase plays, then the angel has failed to be eliminated at the first turn. They now become a regular villager.
        elif phase == Phase.ANGEL_CHECK:
            # Skip phase at turn 0
            if state.turn <= 0:
                state.game_phases.advance_phase()
                return self.step_deals_with_new_phase(state)
            id_angel = self.get_id_player_with_role(state, RoleAngel())
            state.common_obs.add_message(
                "You have failed to be eliminated at the first turn. You are now a regular villager.",
                idx_player=id_angel,
            )
            state.game_phases.advance_phase()
            state.game_phases.remove_phase(Phase.ANGEL_CHECK)
            self.turn_angel_into_villager(state)
            return self.step_deals_with_new_phase(state)

        # Wolfdog Choice phase : ask the wolfdog whether to join the wolves or the villagers, then self-destruct the phase
        elif phase == Phase.WOLFDOG_CHOICE:
            id_wolfdog = self.get_id_player_with_role(state, RoleWolfdog())
            state.common_obs.add_message(
                "You are now given the opportunity to choose your faction. You can either join the wolves or the villagers. If you wish to join the wolves, play the action 'Join wolves'. If you wish to join the villagers, play the action 'Join villagers'.",
                idx_player=id_wolfdog,
            )
            action_space = FiniteActionSpace(actions=["Join wolves", "Join villagers"])
            return self.get_return_feedback_one_player(
                state=state, id_player=id_wolfdog, action_space=action_space
            )

        # Judge Phase : ask the judge to choose whether to create a 2nd vote or not
        elif phase == Phase.JUDGE_PHASE:
            id_judge = self.get_id_player_with_role(state, RoleJudge())
            state.common_obs.add_message(
                "You are now given the opportunity to play your once-per-game power and create a 2nd vote for this day. If you wish to do so, play the action 'Create vote'. If you wish to not create a 2nd vote, play the action 'Do nothing'.",
                idx_player=id_judge,
            )
            action_space = FiniteActionSpace(actions=["Create vote", "Do nothing"])
            return self.get_return_feedback_one_player(
                state=state, id_player=id_judge, action_space=action_space
            )

        # Bear Showman phase : growl in function of the number of players next to the bear showman
        elif phase == Phase.BEAR_SHOWMAN_PHASE:
            id_bear_showman = self.get_id_player_with_role(state, RoleBearShowman())
            id_left = (id_bear_showman - 1) % self.n_players
            while not state.list_are_alive[id_left]:
                id_left = (id_left - 1) % self.n_players
            id_right = (id_bear_showman + 1) % self.n_players
            while not state.list_are_alive[id_right]:
                id_right = (id_right + 1) % self.n_players
            list_ids_next_to_bear = list(set([id_left, id_bear_showman, id_right]))
            n_growls = len(
                [
                    i
                    for i in list_ids_next_to_bear
                    if state.identities[i].have_status(Status.IS_WOLF)
                ]
            )
            n_growls += random.randint(-1, 1)  # Add a random number of growls
            n_growls = max(0, n_growls)  # Ensure the number of growls is positive
            if n_growls >= 1:
                message_growls = "\n".join(["Grrr..." for _ in range(n_growls)])
                state.common_obs.add_global_message(
                    message_growls,
                )
                print(message_growls)
            # Advance to the next phase
            state.game_phases.advance_phase()
            return self.step_deals_with_new_phase(state)

        # Fox phase : ask the fox to smell 3 players
        elif phase == Phase.FOX_PHASE:
            id_fox = self.get_id_player_with_role(state, RoleFox())
            list_id_players_smellable = [
                str(i)
                for i in range(self.n_players)
                if state.list_are_alive[i] and i != id_fox
            ]
            if len(list_id_players_smellable) < 3:
                # If not enough players to smell, skip the phase
                state.game_phases.advance_phase()
                return self.step_deals_with_new_phase(state)
            action_space = K_AmongFiniteActionSpace(
                actions=list_id_players_smellable, k=3
            )
            state.common_obs.add_message(
                (
                    f"Fox, you can now choose 3 players to smell among the alive players : {list_id_players_smellable}.",
                    f"Return your action under the following formalism : '<player_id_1> <player_id_2> <player_id_3>', e.g. '1 2 3'.",
                ),
                idx_player=id_fox,
            )
            return self.get_return_feedback_one_player(
                state=state, id_player=id_fox, action_space=action_space
            )

        # Sister speech phase : ask each sister to send a message to the other sister
        elif phase == Phase.SISTER_SPEECH:
            list_ids_sisters = self.get_id_player_with_role(
                state, RoleSister(), return_list=True
            )
            if len(list_ids_sisters) < 2:
                # If not enough sisters, skip the phase
                state.game_phases.advance_phase()
                return self.step_deals_with_new_phase(state)
            state.common_obs.add_specific_message(
                "You are now given the opportunity to send a message to the other sister.",
                list_idx_player=list_ids_sisters,
            )
            action_space = TextualActionSpace(
                description="Send a message to the other sister."
            )
            return self.get_return_feedback_several_players(
                state=state,
                joint_action_space=[
                    action_space if i in list_ids_sisters else None
                    for i in range(self.n_players)
                ],
            )

        else:
            raise NotImplementedError(f"Phase {phase} not implemented yet.")


    

    

    

        

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

    def get_ids_wolf_victims(self, state: StateWW) -> List[int]:
        ids_wolf_victims = [
            id_player
            for id_player, causes in state.night_attacks.items()
            if CAUSES_OF_DEATH.WOLF_ATTACK in causes
        ]
        assert (
            len(ids_wolf_victims) <= 1
        ), "There should be at most one wolf victim. (Not implemented yet)"
        return ids_wolf_victims

    

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

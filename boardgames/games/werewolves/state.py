from abc import ABC, abstractmethod
from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
import random
from time import sleep
from typing import Any, Dict, List, Optional, Set, Tuple, Type, Union
from boardgames.common_obs import CommonObs
from boardgames.games.werewolves.causes_of_deaths.base_cause import CauseOfDeath
from boardgames.games.werewolves.factions import FactionsWW
from boardgames.games.werewolves.identity import Identity
from boardgames.games.werewolves.phase.base_phase import (
    Phase,
    LIST_NAMES_PHASES_ORDERED,
)
from boardgames.games.werewolves.roles.base_role import RoleWW
from boardgames.games.werewolves.statutes.base_status import Status
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


# Define elementary causes of death
class CauseVote(CauseOfDeath):
    def get_name(self):
        return "Vote"

    def is_day_cause_of_death(self):
        return True

    def get_message_on_death(self, state: "StateWW", id_player: int) -> str:
        return f"Player {id_player} was eliminated by the vote."


class CauseWolfAttack(CauseOfDeath):
    def get_name(self):
        return "Wolf attack"

    def is_day_cause_of_death(self):
        return False


# Define elementary phases
class PhaseDaySpeech(Phase):
    
    def get_name(self) -> str:
        return "Day Speech"

    def is_day_phase(self) -> bool:
        return True

    def play_action(self, state: "StateWW", joint_action: JointAction):
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
            state.phase_manager.advance_phase()
            if state.turn == 0:
                assert (
                    state.phase_manager.get_current_phase().get_name() == "Day Vote"
                ), "Next phase should be the vote phase."
                state.phase_manager.advance_phase()  # Skip the vote phase the first day
            # Reset the speech variables for good measure
            state.order_speech = None
            state.idx_speech = None


    def return_feedback(self, state: "StateWW") -> Tuple[
        JointReward,
        JointPlayingInformation,
        JointObservation,
        JointActionSpace,
        TerminalSignal,
        InfoDict,
    ]:
        if state.order_speech is None:
            # Increment the turn
            state.turn += 1
            # Announce the deaths of the previous night and apply consequences
            if state.turn > 0:  # there is no last night at the first turn
                state.apply_deaths_of_last_night()
            # If game is over, return the victory
            if state.is_game_over():
                return state.step_return_victory_remaining_faction()
            # Announce the beginning of the day speech and set up the speech variables
            state.start_new_day()

        id_player_speaking = state.order_speech[state.idx_speech]
        state.common_obs.add_global_message(
            f"Player {id_player_speaking} is now speaking."
        )
        state.common_obs.add_message(
            text="You are now speaking. Please express yourself about the current situation.",
            idx_player=id_player_speaking,
        )
        return state.get_return_feedback_one_player(
            id_player=id_player_speaking,
            action_space=TextualActionSpace(
                description="Express yourself about the current situation."
            ),
        )


class PhaseDayVote(Phase):
    
    def get_name(self) -> str:
        return "Day Vote"

    def is_day_phase(self) -> bool:
        return True

    def play_action(self, state: "StateWW", joint_action: JointAction):
        report_vote = ""
        vote_count: Dict[int, int] = defaultdict(int)
        list_id_players_alive = [
            i for i in range(state.n_players) if state.list_are_alive[i]
        ]
        # If a player has a Crow malus, add 2 votes against them and remove the malus status
        # for id_player in list_id_players_alive:
        #     if state.identities[id_player].have_status(Status.HAS_CROW_MALUS):
        #         vote_count[id_player] += 2
        #         report_vote += (
        #             f"Crow malus set 2 votes against player {id_player}.\n"
        #         )
        #         state.identities[id_player].remove_status(Status.HAS_CROW_MALUS)
        # Count the votes
        for id_player, id_target in enumerate(joint_action):
            if id_target is not None:
                assert (
                    id_player in list_id_players_alive
                ), f"Player {id_player} is not an alive player but has chosen to vote for player {id_target}."
                assert (
                    id_target in list_id_players_alive
                ), f"Player {id_player} cannot vote for a dead player but player {id_target} is dead."
                report_vote += f"Player {id_player} voted for player {id_target}.\n"
                vote_count[id_target] += 1
        state.common_obs.add_global_message(
            text=f"The players have voted the following : \n{report_vote}",
        )
        most_voted_players = [
            id_player
            for id_player, count in vote_count.items()
            if count == max(vote_count.values())
        ]
        # If there is a draw, pick a player randomly among the tied players
        if len(most_voted_players) > 1:
            id_target_final = random.choice(most_voted_players)
            state.common_obs.add_global_message(
                f"There is a draw in the votes. Eliminated player is picked randomly among the tied players : {id_target_final}."
            )
        else:
            id_target_final = most_voted_players[0]
            state.common_obs.add_global_message(
                f"The most voted player will be eliminated : {id_target_final}."
            )
        # Eliminate the player and apply consequences
        state.apply_death_consequences(id_target_final, CauseVote())
        # Advance to the next phase
        state.phase_manager.advance_phase()

    def return_feedback(self, state: "StateWW") -> Tuple[
        JointReward,
        JointPlayingInformation,
        JointObservation,
        JointActionSpace,
        TerminalSignal,
        InfoDict,
    ]:
        list_id_players_voting = [
            i
            for i in range(state.n_players)
            if (
                state.list_are_alive[i]
                # and not state.identities[i].have_status(Status.CANNOT_VOTE)
            )
        ]
        rewards = [0.0] * state.n_players
        list_is_playing = [i in list_id_players_voting for i in range(state.n_players)]
        list_obs = state.common_obs
        list_action_spaces = []
        for i in range(state.n_players):
            if not state.list_are_alive[i]:
                list_action_spaces.append(None)
            else:
                list_id_other_players_alive_as_str = [
                    str(j)
                    for j in range(state.n_players)
                    if j != i and state.list_are_alive[j]
                ]
                list_action_spaces.append(
                    FiniteActionSpace(
                        actions=list_id_other_players_alive_as_str,  # Player i cannot vote for dead players and himself
                    )
                )
                state.common_obs.add_message(
                    f"The vote of day {state.turn+1} will now take place. Pick a player to eliminate among the remaining other players : {list_id_other_players_alive_as_str}.",
                    idx_player=i,
                )
        list_obs = state.common_obs
        return (
            rewards,
            list_is_playing,
            list_obs,
            list_action_spaces,
            False,
            {},
        )


# Define the manager of phases
class PhasesManagerWW:
    """Manager of the phases of the Werewolves game. It is responsible for the order of the phases and the transitions between them."""

    def __init__(self, list_roles: List[RoleWW]) -> None:
        # Initialize the list of phases as the two base phases
        self.list_phases: List[Phase] = [
            PhaseDaySpeech(),
            PhaseDayVote(),
        ]
        # Collect the phases associated with the roles in the composition
        set_phases_from_roles: Set[Phase] = set()
        for role in list_roles:
            set_phases_from_roles.update(role.get_associated_phases())
        # Extend the list of phases with the phases associated with the roles in the order of the list of phases
        for name_phase in LIST_NAMES_PHASES_ORDERED:
            for phase in set_phases_from_roles:
                if phase.get_name() == name_phase:
                    self.list_phases.append(phase)
        # Initialize the indexes
        self.idx_current_phase = 0
        self.idx_first_night_phase = len(
            [phase for phase in self.list_phases if phase.is_day_phase]
        )
        assert all(
            [
                self.list_phases[i].is_day_phase
                for i in range(self.idx_first_night_phase)
            ]
        ), "The phases should be dividedd in n day phases followed by m night phases, with n+m = len(list_phases)."

    def advance_phase(self) -> None:
        """Advance to the next phase in the list of phases."""
        self.idx_current_phase = (self.idx_current_phase + 1) % len(self.list_phases)
        print(f"Entering phase {self.list_phases[self.idx_current_phase]}")

    def remove_phase(self, phase: Phase) -> None:
        """Remove a phase from the list of phases. Also modifies the phase indexes so that it still points to the same phase.

        Args:
            phase (Phase): the phase to remove
        """
        assert (
            self.list_phases.count(phase) <= 1
        ), f"Phase {phase} to remove should be present only 0 or 1 times, but it is present {self.list_phases.count(phase)} times."
        if self.list_phases.count(phase) == 0:
            return  # nothing to do
        else:
            idx_phase_to_remove = self.list_phases.index(phase)
            assert (
                idx_phase_to_remove != self.idx_current_phase
            ), f"Can't remove the current phase {phase}"
            self.list_phases.pop(idx_phase_to_remove)
            # Update the index of the current phase and the first night phase
            if idx_phase_to_remove <= self.idx_current_phase:
                self.idx_current_phase -= 1
            if phase.is_day_phase:
                self.idx_first_night_phase -= 1

    def insert_phase(self, phase: Phase) -> None:
        """Insert a phase in the list of phases at the next index. Also modifies the first night phase index if necessary.

        Args:
            phase (Phase): the phase to insert
        """
        idx_next_phase = (self.idx_current_phase + 1) % len(self.list_phases)
        self.list_phases.insert(idx_next_phase, phase)
        # Update the index of the first night phase
        if phase.is_day_phase:
            self.idx_first_night_phase += 1

    def get_current_phase(self) -> Phase:
        """Get the current phase."""
        return self.list_phases[self.idx_current_phase]

    def set_current_phase(self, phase: Phase) -> None:
        """Set the current phase to a specific phase."""
        assert (
            phase in self.list_phases
        ), f"Phase {phase} should be in the list of phases."
        self.idx_current_phase = self.list_phases.index(phase)

    def get_first_night_phase(self) -> Optional[Phase]:
        """Get the first night phase.
        The first night phase is the first phase in the list of phases that is a night phase (the list of phases is divided in day phases followed by night phases).

        If there is no night phase but the game continue because there is still more than 2 factions alive, return None.
        """
        if self.idx_first_night_phase == len(self.list_phases):
            return None
        return self.list_phases[self.idx_first_night_phase]

    def __repr__(self):
        return (
            f"[{self.list_phases} at phase {self.list_phases[self.idx_current_phase]}]"
        )


# Define elementary statutes
class StatusIsWolf(Status):
    def get_name(self):
        return "Is Wolf"

    def apply_death_announcement_and_confirm(
        self, state: "StateWW", id_player: int, cause: CauseOfDeath
    ):
        return True

    def apply_death_consequences(
        self, state: "StateWW", id_player: int, cause: CauseOfDeath
    ):
        pass


class StateWW(State):
    """The state of the Werewolves game.
    It contains all the information about the game at a given time, including :
        - the number of players
        - the list of roles
        - the list of identities
        - the composition of the game
        - the phase manager
        - the list of alive players
        - variables related to speeches
        - the night attacks, an object active the night that keeps track of the attacks
        - the common observation, which manage the observation of each player
        - other game variables such as the turn, the index of the subphase...
    """

    def __init__(
        self,
        n_players: int,
        list_roles: List[Type],
        identities: List[Identity],
        compo: Dict[Type, Dict],
        **kwargs,
    ) -> None:
        self.n_players = n_players
        self.list_roles = list_roles
        self.identities = identities
        self.config = kwargs

        # Initialize WW game variables
        self.phase_manager = PhasesManagerWW(list_roles=list_roles)
        print(f"Phases : {self.phase_manager}\n")
        self.done = False
        self.turn = 0
        self.idx_subphase = 0
        self.list_are_alive: List[bool] = [True] * self.n_players
        self.order_speech = None
        self.idx_speech = None
        self.order_speech_wolf = None
        self.idx_speech_wolf = None
        self.night_attacks: Dict[int, Set[CauseOfDeath]] = None
        # Initialize common observation
        self.common_obs = CommonObs(n_players=self.n_players)
        self.common_obs.add_global_message("The game has started.")
        compo_pretty = {k: v["n"] for k, v in compo.items()}
        self.common_obs.add_global_message(
            f"The composition of the game is : {compo_pretty}."
        )
        for id_player, identity in enumerate(self.identities):
            self.common_obs.add_message(
                text=(
                    f"You are player {id_player}. "
                    f"Your role is {identity.role.get_name()}, you win with the faction {identity.faction}. "
                    f"\nDescription of your role : {identity.role.get_textual_description()}"
                ),
                idx_player=id_player,
            )
        # Inform the wolf players of their identity
        list_id_wolves = self.get_list_id_wolves_alive()
        self.common_obs.add_specific_message(
            f"[Private Wolf Chat] You see the wolves are composed of : {list_id_wolves}.",
            list_idx_player=list_id_wolves,
        )
        # Initialize the couple
        if self.config["do_couple"]:
            self.couple = random.sample(range(self.n_players), 2)
            for id1, id2 in [self.couple, self.couple[::-1]]:
                self.identities[id1].add_status(Status.IS_COUPLE_MEMBER)
                self.identities[id1].change_faction(FactionsWW.COUPLE)
                self.common_obs.add_message(
                    text=(
                        f"You fell in love with player {id2}. "
                        f"You must now win together with your lover, no matter the faction."
                        f"You see the role of your lover {id2} is {self.identities[id2].role.get_name()}."
                    ),
                    idx_player=id1,
                )
        else:
            self.couple = None

        return

        assert (RoleHunter() in self.compo) or not (
            RoleRedRidingHood() in self.compo
        ), "Red Riding Hood cannot be in the game without the Hunter."
        if RoleNecromancer() in self.compo:
            self.necromancer_dict: dict = {}
        if RoleMercenary() in self.compo:
            id_mercenary = self.game.get_id_player_with_role(self, RoleMercenary())
            id_mercenary_target = (
                id_mercenary + random.randint(1, self.n_players - 1)
            ) % self.n_players
            self.identities[id_mercenary_target].add_status(Status.IS_MERCENARY_TARGET)
            self.common_obs.add_message(
                text=(
                    f"Your target is player {id_mercenary_target}. "
                    f"If you manage to have them eliminated by the vote at day 2, you will win the game instantly. Otherwise, you will become a villager."
                ),
                idx_player=id_mercenary,
            )
        if RoleAbominableSectarian() in self.compo:
            self.is_victory_abominable_sectarian = False
            if self.n_players % 2 == 1:
                k = random.choice([self.n_players // 2, self.n_players // 2 + 1])
            else:
                k = self.n_players // 2
            id_abominable_sectarian = self.game.get_id_player_with_role(
                self, RoleAbominableSectarian()
            )
            group1 = random.sample(range(self.n_players), k)
            group2 = list(set(range(self.n_players)) - set(group1))
            if id_abominable_sectarian in group1:
                group_excluding_abominable_sectarian = group2
            else:
                group_excluding_abominable_sectarian = group1
            for id_player in group_excluding_abominable_sectarian:
                self.identities[id_player].add_status(
                    Status.DONT_BELONG_TO_ABOMINABLE_SECTARIAN_GROUP
                )
            self.common_obs.add_global_message(
                (
                    f"Their is an Abominable Sectarian in the game. They will win if they manage to eliminate all players not in their group while staying alive. \n"
                    f"Group 1 is composed of players {group1}. \n"
                    f"Group 2 is composed of players {group2}. \n"
                    f"You do not know in which group is the Abominable Sectarian."
                )
            )
            self.common_obs.add_message(
                text=(
                    f"You are the Abominable Sectarian. You must eliminate all players in the opposite group : {group_excluding_abominable_sectarian}."
                ),
                idx_player=id_abominable_sectarian,
            )
        if RoleWildChild() in self.compo:
            id_wild_child = self.game.get_id_player_with_role(self, RoleWildChild())
            id_tutor = (
                id_wild_child + random.randint(1, self.n_players - 1)
            ) % self.n_players
            self.identities[id_tutor].add_status(Status.IS_WILD_CHILD_TUTOR)
            self.common_obs.add_message(
                f"Your tutor was chosen to be player {id_tutor}.",
                idx_player=id_wild_child,
            )
        if RoleVillagerVillager() in self.compo:
            id_villager_villager = self.game.get_id_player_with_role(
                self, RoleVillagerVillager()
            )
            self.common_obs.add_global_message(
                (
                    f"Player {id_villager_villager} is a Villager Villager. Their role is publicly known to all players."
                )
            )
        if RoleSister() in self.compo:
            assert (
                self.compo[RoleSister()] == 2
            ), "There must be exactly 2 Sisters (or none)."
            self.sisters = self.game.get_id_player_with_role(
                self, RoleSister(), return_list=True
            )
            for id1, id2 in [self.sisters, self.sisters[::-1]]:
                self.common_obs.add_message(
                    text=(
                        f"You are a Sister. You know the identity of your sister : {id2}."
                    ),
                    idx_player=id1,
                )

    # ===== Active methods =====

    def start_new_day(self):
        """Start a new day speech. It initialize day speech variables and also add the new day message to the common observation.

        Args:
            state (StateWW): the current state of the game
        """
        # Start a new day speech
        self.common_obs.add_global_message(
            f"Day {self.turn+1} has started. Players will now be able to speak in a random order before the vote.",
        )
        # Define the order of speech
        list_id_players_alive = [
            i for i in range(self.n_players) if self.list_are_alive[i]
        ]
        self.order_speech = list_id_players_alive.copy()
        random.shuffle(self.order_speech)  # TODO : uncomment this line
        self.idx_speech = 0

    def start_new_night_wolf_speech(self):
        """Start a new night wolf speech. It initialize night wolf speech variables and also add the new night message to the wolf observations.

        Args:
            state (StateWW): the current state of the game
        """
        # Start a new day speech
        list_id_wolves_alive = self.get_list_id_wolves_alive()
        self.common_obs.add_specific_message(
            f"[Private Wolf Chat] Night {self.turn+1} has started. You and the other wolves will now be able to speak in private, in a random order, before choosing your target. You must choose wisely.",
            list_idx_player=list_id_wolves_alive,
        )
        # Define the order of speech
        self.order_speech_wolf = list_id_wolves_alive.copy()
        random.shuffle(self.order_speech_wolf)
        self.idx_speech_wolf = 0

    def apply_deaths_of_last_night(self):
        """Announce the deaths of the last night and update the state of the game.

        Args:
            state (StateWW): the current state of the game
        """
        self.common_obs.add_global_message(
            f"Night {self.turn} is over. The village awaken."
        )
        # if (
        #     self.night_attacks == RoleJudge.ABSENT_NIGHT_INDICATOR
        # ):  # happens if Judge decided to create a 2nd vote
        # pass
        if len(self.night_attacks) == 0:
            self.common_obs.add_global_message("No one has died during the night.")
        else:
            items = list(self.night_attacks.items())
            random.shuffle(items)  # Randomize the order of the deaths to avoid bias
            for id_player, causes in self.night_attacks.items():
                for cause in causes:
                    self.apply_death_consequences(id_player, cause)
        self.night_attacks = None  # Reset the night deaths for good measure

    def apply_death_consequences(
        self,
        id_player: int,
        cause: CauseOfDeath,
    ):
        """Apply the consequences of a player supposed to die of a given cause of death.
        
        If the player is not supposed to die, this won't do anything as the player is already dead.
        
        It does th following :
            - apply any events supposed to happen if the player is announced dead, regarding its role, statutes and the cause of death.
            If the player is not supposed to die because any of these events prevent it, this won't kill the player and stop the process here.
            - kill the player
            - inform the board and the player of the death, and publicly reveal its role
            - apply any events supposed to happen if the  player actually dies, regarding its role, statutes and the cause of death.

        Args:
            id_player (int): _description_
            cause (CauseOfDeath): _description_
        """
        # Skip if the player is already dead
        if not self.list_are_alive[id_player]:
            return

        role_eliminated_player = self.identities[id_player].role
        statutes_eliminated_player = self.identities[id_player].statutes

        # Deal with special cases that prevent the player from dying
        is_death_confirmed = True
        if not role_eliminated_player.apply_death_announcement_and_confirm(
            self, id_player, cause
        ):
            is_death_confirmed = False
            raise
        for status in statutes_eliminated_player:
            if not status.apply_death_announcement_and_confirm(self, id_player, cause):
                is_death_confirmed = False
                raise
        if not cause.apply_death_announcement_and_confirm(self, id_player):
            is_death_confirmed = False
            breakpoint()
        if not is_death_confirmed:
            return

        # Kill the player
        self.list_are_alive[id_player] = False

        # Remove the phase associated with the role of the player
        for phase in role_eliminated_player.get_associated_phases():
            self.phase_manager.remove_phase(phase)
            
        # Inform the board and the player of the death
        if not cause.is_day_cause_of_death():
            self.common_obs.add_global_message(
                f"Player {id_player} has died during the night."
            )
        else:
            message_cause_of_death = cause.get_message_on_death(self, id_player)
            self.common_obs.add_global_message(message_cause_of_death)

        self.common_obs.add_global_message(
            f"The role of player {id_player} was {role_eliminated_player}."
        )
        self.common_obs.add_message(
            f"You have been eliminated from the game.",
            idx_player=id_player,
        )

        # Deal with special cases of consequences of the death
        role_eliminated_player.apply_death_consequences(self, id_player, cause)
        for status in statutes_eliminated_player:
            status.apply_death_consequences(self, id_player, cause)
        cause.apply_death_consequences(self, id_player)
        return

    # ===== Getter/Checker methods =====

    def is_game_over(self) -> bool:
        """Check if the game is over for faction reasons, ie. if there is only one faction alive.

        Returns:
            bool: whether the game is over (for faction reasons : only one faction alive)
        """
        set_factions_alive = {
            self.identities[i].faction
            for i in range(self.n_players)
            if self.list_are_alive[i]
        }
        return len(set_factions_alive) <= 1

    def get_return_feedback_one_player(
        self, id_player: int, action_space: ActionsSpace
    ) -> Tuple[
        JointReward,
        JointPlayingInformation,
        JointObservation,
        JointActionSpace,
        bool,
        Dict,
    ]:
        """Return the .step() returns in the case of only one player play this round.

        Args:
            id_player (int): the id of the player playing
            action_space (ActionsSpace): the action space of the player

        Returns:
            Tuple[JointReward, JointPlayingInformation, JointObservation, JointActionSpace, bool, Dict, ]: the .step() returns
        """
        rewards = [0.0] * self.n_players
        list_is_playing = self.empty_list_except(idx=id_player, value=True, fill=False)
        list_obs = self.empty_list_except(
            idx=id_player, value=self.common_obs[id_player], fill=None
        )
        list_action_spaces = self.empty_list_except(
            idx=id_player, value=action_space, fill=None
        )
        return (
            rewards,
            list_is_playing,
            list_obs,
            list_action_spaces,
            False,
            {},
        )

    def get_list_id_players_alive(self) -> List[int]:
        """Return the list of the ids of the players that are still alive in the game.

        Returns:
            List[int]: the list of the ids of alive players
        """
        return [i for i in range(self.n_players) if self.list_are_alive[i]]
    
    def get_list_id_wolves_alive(self) -> List[int]:
        """Return the list of the ids of the wolves that are still alive in the game.

        Returns:
            List[int]: the list of the ids of alive wolves
        """
        return [
            i
            for i in range(self.n_players)
            if (
                self.identities[i].have_status(StatusIsWolf())
                and self.list_are_alive[i]
            )
        ]

    def get_ids_wolf_victims(self) -> List[int]:
        ids_wolf_victims = [
            id_player
            for id_player, causes in self.night_attacks.items()
            if CauseWolfAttack() in causes
        ]
        assert (
            len(ids_wolf_victims) <= 1
        ), "There should be at most one wolf victim. (Not implemented yet)"
        return ids_wolf_victims
    
    # ===== Victory returns methods =====

    def step_return_victory_remaining_faction(
        self, dont_return_state: bool = True
    ) -> Tuple:
        """Perform the return feedback step when the game is over for faction reasons (only one faction alive).

        Args:
            dont_return_state (bool, optional): whether to not include the state in the return. Defaults to True (step_return_feedback returns).

        Returns:
            Tuple: the .step() returns
        """
        set_factions_alive = {
            self.identities[i].faction
            for i in range(self.n_players)
            if self.list_are_alive[i]
        }
        # If all players are dead, it is a draw
        if len(set_factions_alive) == 0:
            assert all(
                not self.list_are_alive[i] for i in range(self.n_players)
            ), "All players should be dead."
            self.common_obs.add_global_message(
                "All players are dead. The game is a draw."
            )
            return self.step_return_victory_of_faction(
                self, None, dont_return_state=dont_return_state
            )
        elif len(set_factions_alive) == 1:
            faction_winner = set_factions_alive.pop()
            assert all(
                self.identities[i].faction == faction_winner
                for i in range(self.n_players)
                if self.list_are_alive[i]
            ), f"All alive players should be in the same faction : {faction_winner}."
            self.common_obs.add_global_message(
                f"All players alive are in the faction {faction_winner}. The game is won by the {faction_winner}."
            )
            return self.step_return_victory_of_faction(
                faction_winner, dont_return_state=dont_return_state
            )
        else:
            raise ValueError(
                f"Multiple factions are alive : {set_factions_alive}. This should not happen."
            )

    def step_return_victory_of_faction(
        self, faction: Union[FactionsWW, List[FactionsWW]], dont_return_state: bool = True
    ) -> Tuple:
        """Perform the return feedback step when the game is won by a faction or a group of factions.
        Winning players will receive a reward of 1.0, losing players will receive a reward of -1.0.
        In case of a draw, all players will receive a reward of 0.0.
        
        Args:
            faction (Union[FactionsWW, List[FactionsWW]]): the faction or list of factions that won the game
            dont_return_state (bool, optional): whether to not include the state in the return. Defaults to True (step_return_feedback returns).

        Returns:
            Tuple: the .step() returns
        """
        if faction is None:
            rewards = [0.0] * self.n_players
            info = {"result": "Draw"}
        elif isinstance(faction, list):
            assert (
                len(faction) >= 2
            ), "There should be at least two factions for this function to be called."
            rewards = [
                (1.0 if self.identities[i].faction in faction else -1.0)
                for i in range(self.n_players)
            ]
            info = {"result": f"Together in victory : {', '.join(faction)}"}
        else:
            rewards = [
                (1.0 if self.identities[i].faction == faction else -1.0)
                for i in range(self.n_players)
            ]
            info = {"result": f"Win by {faction}"}
        list_is_playing = [False] * self.n_players
        list_obs = self.common_obs
        list_action_spaces = [None] * self.n_players
        done = True
        self.done = True
        if dont_return_state:
            return (
                rewards,
                list_is_playing,
                list_obs,
                list_action_spaces,
                done,
                info,
            )
        else:
            return (
                rewards,
                self,
                list_is_playing,
                list_obs,
                list_action_spaces,
                done,
                info,
            )

    # ===== Helper methods =====
    
    def empty_list_except(
        self, idx: Union[int, List[int]], value: Any, fill: Any = None
    ) -> List[Any]:
        """Create a list of size n_players with all elements set to fill except the one at idx set to value.

        Args:
            idx (Union[int, List[int]]): the index or list of indices to set to
            value (Any): the value to set at index idx
            fill (Any, optional): the fill value. Defaults to None.

        Returns:
            List[Any]: the list of n_players elements
        """
        if isinstance(idx, int):
            idx = [idx]
        list = [fill for _ in range(self.n_players)]
        for i in idx:
            list[i] = value
        return list

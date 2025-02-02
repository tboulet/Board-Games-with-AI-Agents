from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional, Tuple

from boardgames.action_spaces import JointActionSpace
from boardgames.types import (
    InfoDict,
    JointAction,
    JointObservation,
    JointPlayingInformation,
    JointReward,
    State,
    TerminalSignal,
)


class Phase(ABC):
    """A phase of the game.
    It describes :
        - how an action a_t will impact the state of the game during this phase, changing it from s_t_begin to s_t_end
        - when entering the phase after any previous action a_t was played during the play_action part,
        what happens to the state (changing it from s_t_end to s_t+1_begin) and what feedback should be returned to the agents

    The dynamic of the game (game.step() method) is the following:

    def step(self, joint_action: JointAction) -> Tuple[State, JointReward, JointPlayingInformation, JointObservation, JointActionSpace, TerminalSignal, InfoDict]:

        # Play the action in the current phase
        phase = state.game_phases.get_current_phase()
        phase.play_action(state, joint_action)

        # Check if the game is over (irrelevant for the phase)
        if state.is_game_over():
            return state.step_return_victory_remaining_faction()

        # Play second part and return feedback
        phase = state.game_phases.get_current_phase()
        deals_with_entering_new_night (irrelevant for the phase)
        return phase.return_feedback(state)

    Additionally, the name of the phase (get_name method) should appear in the list LIST_NAMES_PHASES_ORDERED in the order of the phases in the game.
    This will allow the game to know the order in which the phases should be played.
    """

    def __init__(self, id_player: Optional[int] = None):
        """Initialize the phase.

        Args:
            id_player (Optional[int], optional): the id of the player playing in this phase. Defaults to None.
        """
        self.id_player: int = id_player

    # ==== Interface methods to implement ====

    @abstractmethod
    def get_name(self) -> str:
        """Get the name of the phase.

        Returns:
            str: the name of the phase
        """
        pass

    @abstractmethod
    def is_day_phase(self) -> bool:
        """Whether the phase is a day phase or not.

        A day phase is a phase that plays during the day.
        It is usually public and action performed are seen by all players (unless certain roles that act privately during the day).

        Night phases are phases that play during the night.
        It is usually private and actions performed are seen by a restricted number of players.

        Returns:
            bool: whether the phase is a day phase
        """
        pass

    @abstractmethod
    def play_action(self, state: State, joint_action: JointAction):
        """Play the action in the current phase.
        This method should modify the state of the game according to the joint action played during this phase.

        Args:
            state (State): the current state of the game
            joint_action (JointAction): a joint action (list of action of size n_players, with None for non-playing players)
        """
        pass

    @abstractmethod
    def return_feedback(self, state: State) -> Tuple[
        JointReward,
        JointPlayingInformation,
        JointObservation,
        JointActionSpace,
        TerminalSignal,
        InfoDict,
    ]:
        """Play the second part of the phase and return the feedback to the agents.
        This method should (possibly) modify the state of the game.
        It should then return the feedback to the agents.

        Args:
            state (State): the current state of the game

        Returns:
            JointReward: the reward for each player, as a list of n_players floats
            JointPlayingInformation: a boolean list of n_players indicating whether the player will play in the next phase
            JointObservation: the observation for each player, as a list of n_players observations
            JointActionSpace: the action space for each player, as a list of n_players action spaces, with None for non-playing players
            TerminalSignal: the terminal signal (done) indicating whether the game is over
            InfoDict: a dictionary of additional information for logging purposes
        """
        pass

    # ==== Default methods ====

    def __repr__(self):
        return self.get_name()

    def __eq__(self, other: "Phase") -> bool:
        """Two phases are equal if they have the same name and the same player id.
        This method can be overriden for more complex phases.
        """
        return self.get_name() == other.get_name()

    def __hash__(self):
        return hash(self.get_name())


LIST_NAMES_PHASES_ORDERED = [
    "Day Speech",
    "Day Vote",
    "Angel Check",
    "Announcement Night",
    "Bodyguard Phase",
    "Night Wolf Speech",
    "Night Wolf Vote",
    "Infection Phase",
    "White Wolf Attack",
    "Seer Phase",
    "Witch Phase",
    "Hunter Choice",
    "Gravedigger Choice",
    "Necromancer Phase",
    "Thief Phase",
    "Crow Phase",
    "Invisible Phase",
    "Perfidious Wolf Attack",
    "Mercenary Check",
    "Pyromancer Phase",
    "Wolfdog Choice",
    "Judge Phase",
    "Bear Showman Phase",
    "Fox Phase",
    "Sister Speech",
]

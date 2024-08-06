from abc import ABC, abstractmethod
from typing import List, Tuple, Union
import numpy as np
from boardgames.types import Observation, Action, State, AgentID, RewardVector


class BaseGame(ABC):

    @abstractmethod
    def reset(self) -> Tuple[State, Observation, AgentID, dict]:
        """Reset the game to its initial state and return the initial observation and state.

        Returns:
            State: the initial state of the game
            Observation: the observation of the first player
            AgentID: the id of the first player
            dict: additional information
        """
        pass

    @abstractmethod
    def step(
        self, state: State, action: Action
    ) -> Tuple[State, Observation, RewardVector, AgentID, bool, dict]:
        """Perform one step of the game.

        Args:
            state (State): the current state of the game
            action (Action): the action to perform

        Returns:
            State: the new state of the game
            Observation: the observation of the next player
            RewardVector: the reward vector obtained by each player
            AgentID: the id of the next player
            bool: whether the game is over
            dict: additional information
        """
        pass

    @abstractmethod
    def get_actions_available(self, state: State) -> List[Action]:
        """Return the list of actions available in the current state.

        Args:
            state (State): the current state of the game

        Returns:
            List[Action]: the list of actions available
        """
        pass

    def get_n_players(self) -> int:
        """Return the number of players in the game.

        Returns:
            int: the number of players
        """
        pass

    def render(self, state: State) -> None:
        """Render the current state of the game.

        Args:
            state (State): the current state of the game
        """
        pass

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple, Union
import numpy as np
from boardgames.types import Observation, Action, State, AgentID
from boardgames.action_spaces import ActionsSpace

class BaseGame(ABC):

    def __init__(self, n_players: int):
        self.n_players = n_players

    @abstractmethod
    def reset(
        self,
    ) -> Tuple[State, List[bool], List[Observation], List[ActionsSpace], Dict]:
        """Reset the game to its initial state and return the initial observation and state.

        Returns:
            State: the initial state of the game
            List[bool]: the list of players playing (True) or not playing (False)
            List[Observation]: the initial observation of each player (None if not playing)
            List[ActionsSpace]: the list of actions spaces available for each player (None if not playing)
            Dict: additional information
        """
        pass

    @abstractmethod
    def step(self, state: State, list_actions: List[Action]) -> Tuple[
        List[float],
        State,
        List[bool],
        List[Observation],
        List[ActionsSpace],
        bool,
        Dict,
    ]:
        """Execute one step of the game.

        Args:
            state (State): the current state of the game
            list_actions (List[Action]): the list of actions to execute

        Returns:
            List[float]: the reward for each player
            State: the new state of the game
            List[bool]: the next list of players playing (True) or not playing (False)
            List[Observation]: the next observation of each player (None if not playing)
            List[ActionsSpace]: the next list of actions spaces available for each player (None if not playing)
            Dict: additional information
        """
        pass

    @abstractmethod
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

    # ======================== Helper functions ========================

    def empty_list_except(self, idx: int, value: Any, fill: Any = None) -> List[Any]:
        """Create a list of size n_players with all elements set to fill except the one at idx set to value.

        Args:
            idx (int): the index of the value to set
            value (Any): the value to set at index idx
            fill (Any, optional): the fill value. Defaults to None.

        Returns:
            List[Any]: the list of n_players elements
        """
        list = [fill for _ in range(self.n_players)]
        list[idx] = value
        return list

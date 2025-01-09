from abc import ABC, abstractmethod
from enum import Enum
import random
from typing import Dict, List, Optional, Tuple, Union
import numpy as np
from boardgames.games.base_game import BaseGame
from boardgames.types import Observation, Action, State, AgentID
from boardgames.common_obs import CommonObs
from boardgames.action_spaces import ActionsSpace


class BaseTextBasedGame(BaseGame):
    """
    Base class for a game that is supposed to be played by LLM agents and other agents that can interact with text-based games.
    """

    @abstractmethod
    def get_game_context(self) -> str:
        """Provide a description of the game, in order to teach the agent the rules of the game.

        Returns:
            str: a description of the game
        """
        pass

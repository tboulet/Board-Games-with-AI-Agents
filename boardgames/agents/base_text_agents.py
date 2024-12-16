from abc import abstractmethod
from typing import Dict, List

import numpy as np
from boardgames.agents.base_agents import BaseAgent
from boardgames.types import Observation, Action, State, AgentID

import random


class BaseTextAgent(BaseAgent):
    """
    Base class for a text-based agent.
    """

    @abstractmethod
    def set_game_context(self, game_context: str) -> None:
        """Treat the game context provided by the game.

        Args:
            game_context (str): the game context
        """
        pass

from abc import ABC, abstractmethod
from typing import Dict, List

import numpy as np

from boardgames.types import (
    Observation,
    Action,
    State,
    AgentID,
    RewardVector,
)
from boardgames.action_spaces import ActionsSpace


class BaseAgent(ABC):

    @abstractmethod
    def act(self, observation: Observation, action_space: ActionsSpace) -> Action:
        pass

    @abstractmethod
    def learn(
        self,
        is_playing: bool,
        action_space: ActionsSpace,
        observation: Observation,
        action: Action,
        reward: float,
        next_is_playing: bool,
        next_observation: Observation,
        next_action_space: ActionsSpace,
        done: bool,
    ):
        pass

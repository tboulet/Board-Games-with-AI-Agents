from abc import ABC, abstractmethod
from typing import Dict, List

import numpy as np

from boardgames.types import ActionsAvailable, Observation, Action, State, AgentID, RewardVector


class BaseAgent(ABC):

    @abstractmethod
    def act(self, observation: Observation, actions_available: List[Action]) -> Action:
        pass

    @abstractmethod
    def learn(
        self,
        is_playing: bool,
        actions_available: ActionsAvailable,
        observation: Observation,
        action: Action,
        reward: float,
        next_is_playing: bool,
        next_observation: Observation,
        next_actions_available: ActionsAvailable,
        done: bool,
    ):
        pass

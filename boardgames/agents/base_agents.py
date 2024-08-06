from abc import ABC, abstractmethod
from typing import Dict, List

import numpy as np

from boardgames.types import Observation, Action, State, AgentID, RewardVector


class BaseAgent(ABC):

    @abstractmethod
    def act(self, observation : Observation, actions_available : List[Action]) -> Action:
        pass

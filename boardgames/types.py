from abc import ABC, abstractmethod
from typing import List


class State:
    pass


class Observation:
    pass


class Action:
    pass



class AgentID(ABC):
    @abstractmethod
    def __hash__(self) -> int:
        raise NotImplementedError


class RewardVector(list):
    pass

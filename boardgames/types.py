from abc import ABC, abstractmethod
from typing import List


class State:
    pass


class Observation:
    pass


class JointObservation(List[Observation]):
    pass


class Action:
    pass


class JointAction(List[Action]):
    pass


class Reward(float):
    pass


class JointReward(List[Reward]):
    pass


class PlayingInformation:
    pass


class JointPlayingInformation(List[PlayingInformation]):
    pass


class InfoDict(dict):
    pass


class TerminalSignal:
    pass


class AgentID(ABC):
    @abstractmethod
    def __hash__(self) -> int:
        raise NotImplementedError

from abc import ABC, abstractmethod
from enum import Enum
from typing import Tuple

from boardgames.action_spaces import JointActionSpace
from boardgames.types import InfoDict, JointAction, JointObservation, JointPlayingInformation, JointReward, State, TerminalSignal


class Phase(ABC):
    
    @abstractmethod
    def get_name(self) -> str:
        pass
    
    @abstractmethod
    def is_day_phase(self) -> bool:
        pass
    
    @abstractmethod
    def play_action(self, state: State, joint_action: JointAction) -> State:
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
        pass
    
    def __repr__(self):
        return self.get_name()
    
LIST_NAMES_PHASES_ORDERED = [
    "Day Speech",
    "Day Vote",
    "Victory Check",
    "Savior Phase",
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
    "Angel Check",
    "Wolfdog Choice",
    "Judge Phase",
    "Bear Showman Phase",
    "Fox Phase",
    "Sister Speech"
]
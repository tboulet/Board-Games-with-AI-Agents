from abc import ABC, abstractmethod
from enum import Enum
import random
from typing import Dict, Iterable, List, Optional, Tuple, Union
from boardgames.types import Observation, Action, State, AgentID

class ActionsSpace:
    """An object that describes the space in which the players can act.
    It is both informative as textual description with the method get_textual_restrictions and as a container with the method __contains__.
    """
    
    @abstractmethod
    def get_textual_restrictions(self) -> str:
        """Return a textual description of the restrictions of the action space.
        """
        return "Any action is allowed."
    
    @abstractmethod
    def __contains__(self, action: Action) -> bool:
        """Check if an action is in the action space.
        """
        return True
    
    
    
class FiniteActionSpace(ActionsSpace):
    
    def __init__(self, actions: Iterable[Action]):
        self.actions = actions
        
    def get_textual_restrictions(self):
        return "Only the following actions are allowed: " + str(self.actions)
    
    def __contains__(self, action: Action):
        return action in self.actions
    

class TextualActionSpace(ActionsSpace):
    
    def __init__(self, description: str):
        self.description = description
        
    def get_textual_restrictions(self):
        return self.description
    
    def __contains__(self, action: Action):
        return isinstance(action, str)
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
        """Return a textual description of the restrictions of the action space."""
        return "Any action is allowed."

    @abstractmethod
    def __contains__(self, action: Action) -> bool:
        """Check if an action is in the action space."""
        return True


class JointActionSpace(List[ActionsSpace]):
    def __contains__(self, joint_action: List[Action]) -> bool:
        return all(action in actions for action, actions in zip(joint_action, self))


class FiniteActionSpace(ActionsSpace):

    def __init__(self, actions: Iterable[Action]):
        assert len(actions) > 0, "The list of actions must not be empty."
        self.actions = actions

    def get_textual_restrictions(self):
        return "Only the following actions are allowed: " + str(self.actions)

    def __contains__(self, action: Action):
        return action in self.actions


class K_AmongFiniteActionSpace(ActionsSpace):

    def __init__(self, actions: Iterable[Action], k: int):
        self.actions = actions
        self.k = k
        assert 0 < k <= len(actions)

    def get_textual_restrictions(self):
        return (
            f"Return {self.k} non identical actions among the following: {self.actions}, e.g. '{' '.join(str(a) for a in self.actions[:self.k])}'"
        )

    def __contains__(self, action: Action):
        return (
            isinstance(action, list)
            and len(action) == self.k
            and all(a in self.actions for a in action)
            and len(set(action)) == self.k
        )


class TextualActionSpace(ActionsSpace):

    def __init__(self, description: str):
        self.description = description

    def get_textual_restrictions(self):
        return self.description

    def __contains__(self, action: Action):
        return isinstance(action, str)

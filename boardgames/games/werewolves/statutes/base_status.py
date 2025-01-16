from abc import ABC, abstractmethod
from enum import Enum
from typing import Set

from boardgames.games.werewolves.causes_of_deaths.base_cause import CauseOfDeath
from boardgames.types import State


class Status(ABC):

    @abstractmethod
    def get_name(self) -> str:
        """Get the name of the status.

        Returns:
            str: the name of the status
        """
        pass

    def apply_death_announcement_and_confirm(
        self, state: State, id_player: int, cause: CauseOfDeath
    ) -> bool:
        """Apply any events supposed to happen due to that status if the player is announced dead.

        Args:
            state (State): the current state of the game
            id_player (int): the id of the player who died
            cause (CauseOfDeath): the cause of death

        Returns:
            bool: whether the death is confirmed
        """
        return True

    def apply_death_consequences(
        self, state: State, id_player: int, cause: CauseOfDeath
    ):
        """Apply any events due to this status of the death of the player.

        Args:
            state (State): the current state of the game
            id_player (int): the id of the player who died
            cause (CauseOfDeath): the cause of death of the player
        """
        pass

    def apply_protection_status(
        self,
        state: State,
        id_player: int,
    ) -> bool:
        """Apply on the set of death causes the eventual protection of the status.
        This is useful for statuses that can protect a player from dying at night.

        Args:
            state (State): the current state of the game
            id_player (int): the id of the player who has the status
        """
        pass

    # ===== Helper methods =====

    def __repr__(self):
        """By default, the representation of a status is its name.
        This method can be overriden if needed.
        """
        return self.get_name()

    def __eq__(self, other: "Status") -> bool:
        """By default, two statuses are equal if they have the same name.
        This method can be overriden if needed.
        """
        return self.get_name() == other.get_name()


class StatusBaseProtection(Status):

    @abstractmethod
    def apply_protection_status(
        self,
        state: State,
    ) -> bool:
        raise NotImplementedError("This method should be implemented in the subclass.")

from abc import ABC, abstractmethod
from enum import Enum

from boardgames.games.werewolves.causes_of_deaths.base_cause import CauseOfDeath
from boardgames.types import State


class Status(ABC):

    @abstractmethod
    def get_name(self) -> str:
        pass

    def apply_death_announcement_and_confirm(
        self, state: State, id_player: int, cause: CauseOfDeath
    ) -> bool:
        pass

    def apply_death_consequences(
        self, state: State, id_player: int, cause: CauseOfDeath
    ):
        pass

    # ===== Helper methods =====

    def __repr__(self):
        return self.get_name()

    def __eq__(self, other: "Status") -> bool:
        return self.get_name() == other.get_name()

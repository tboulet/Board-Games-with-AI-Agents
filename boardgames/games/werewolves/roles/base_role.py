from abc import ABC, abstractmethod
from typing import List
from boardgames.games.werewolves.causes_of_deaths.base_cause import CauseOfDeath
from boardgames.games.werewolves.factions import FactionsWW
from boardgames.games.werewolves.phase.base_phase import Phase
from boardgames.games.werewolves.statutes.base_status import Status
from boardgames.types import State


class RoleWW(ABC):
    def __init__(self, **kwargs):
        self.is_win_condition_achieved = False
        self.config = kwargs
        super().__init__()

    @classmethod
    @abstractmethod
    def get_name(cls) -> str:
        pass

    @abstractmethod
    def get_initial_faction(self) -> FactionsWW:
        pass

    @abstractmethod
    def get_initial_statutes(self) -> List[Status]:
        pass

    @abstractmethod
    def get_associated_phases(self) -> List[Phase]:
        pass

    @abstractmethod
    def get_textual_description(self) -> str:
        pass

    @abstractmethod
    def initialize_role(self, state: State):
        pass

    def apply_death_announcement_and_confirm(
        self, state: State, id_player: int, cause: CauseOfDeath
    ) -> bool:
        return True

    def apply_death_consequences(
        self, state: State, id_player: int, cause: CauseOfDeath
    ):
        pass

    # ===== Helper methods =====

    def __repr__(self):
        return f"{self.get_name()} ({self.get_initial_faction()})"

    def __eq__(self, other: "RoleWW") -> bool:
        return self.get_name() == other.get_name()

    def __hash__(self) -> int:
        return hash(self.get_name())

    def get_appearance_name(self) -> str:
        return self.get_name()

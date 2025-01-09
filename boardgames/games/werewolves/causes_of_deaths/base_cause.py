from abc import ABC, abstractmethod
from enum import Enum

from boardgames.types import State


class CauseOfDeath(ABC):

    def apply_death_announcement_and_confirm(
        self, state: State, id_player: int
    ) -> bool:
        return True

    def apply_death_consequences(self, state: State, id_player: int):
        pass

    @abstractmethod
    def get_name(self) -> str:
        pass

    @abstractmethod
    def is_day_cause_of_death(self) -> bool:
        pass

    @abstractmethod
    def get_message_on_death(self, state: State, id_player: int) -> str:
        pass


    # # Day causes of death
    # VOTE = "Vote"
    # HUNTER_SHOT = "Hunter Shot"
    # LOVE = "Love"

    # # Night causes of death
    # WOLF_ATTACK = "Wolf Attack"
    # WHITE_WOLF_ATTACK = "White Wolf Attack"
    # WITCH_DEATH_POTION = "Witch Death Potion"
    # INVISIBLE_ATTACK_LITTLE_GIRL = "Invisible Attack Little Girl"
    # INVISIBLE_ATTACK_PERFIDIOUS_WOLF = "Invisible Attack Perfidious Wolf"
    # INVISIBLE_ATTACK_SPIRIT = "Invisible Attack Spirit"
    # FAILED_INVISIBLE_ATTACK = "Failed Invisible Attack"
    # PERFIDIOUS_WOLF_ADDITIONAL_ATTACK = "Perfidious Wolf Additional Attack"

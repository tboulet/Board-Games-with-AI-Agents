from abc import ABC, abstractmethod
from enum import Enum

from boardgames.types import State


class CauseOfDeath(ABC):

    # ==== Interface methods to implement ====
    
    @abstractmethod
    def get_name(self) -> str:
        """Get the name of the cause of death.

        Returns:
            str: the name of the cause of death
        """
        pass

    @abstractmethod
    def is_day_cause_of_death(self) -> bool:
        """Return whether the cause of death comes from an action taking place at day,
        or at night.

        Returns:
            bool: whether it is a day cause of death
        """
        pass
    
    # ===== Methods for specific causes =====
    
    def apply_death_announcement_and_confirm(
        self, state: State, id_player: int
    ) -> bool:
        """Apply any events supposed to happen due to that cause if the player is announced dead.
        If the player is not supposed to die, return False.
        Else, return True (default).

        Args:
            state (State): the current state of the game
            id_player (int): the id of the player who died

        Returns:
            bool: whether the death is confirmed
        """
        return True

    def apply_death_consequences(self, state: State, id_player: int):
        """Apply any events due to this cause of death.
        By default, it does nothing.
        
        Args:
            state (State): the current state of the game
            id_player (int): the id of the player who died
        """
        pass
    
    def get_message_on_death(self, state: State, id_player: int) -> str:
        """Return the message to display when the player dies.
        By default, it return a night cause message indicating that the player died this night without any further information.
        Args:
            state (State): the current state of the game
            id_player (int): the id of the player who died

        Returns:
            str: the message to display
        """
        assert not self.is_day_cause_of_death(), "This method should be overriden for day causes of death."
        return f"Player {id_player} died this night."
    
    # ===== Helper methods =====
    
    def __repr__(self):
        """By default, the representation of a cause of death is its name."""
        return self.get_name()
    
    def __eq__(self, other: "CauseOfDeath") -> bool:
        """By default, two causes of death are equal if they have the same name.
        This method can be overriden if needed.
        """
        return self.get_name() == other.get_name()
    
    def __hash__(self) -> int:
        return hash(self.get_name())

    


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

from abc import ABC, abstractmethod
from typing import Any, List
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

    def set_id_player(self, id_player: int):
        """Set the id of the player having this role."""
        self.id_player = id_player

    # ===== Role interface to implement by subclasses =====

    @classmethod
    @abstractmethod
    def get_name(cls) -> str:
        """Return the name of the role.

        Returns:
            str: the name of the role
        """
        pass

    @classmethod
    @abstractmethod
    def get_initial_faction(cls) -> FactionsWW:
        """Return the initial faction of the role.
        This is the faction the role should initially belong to,
        although the faction of the player can change during the game.

        Returns:
            FactionsWW: the initial faction of the role
        """
        pass

    @abstractmethod
    def get_initial_statutes(self) -> List[Status]:
        """Return the initial statutes of the role.

        Returns:
            List[Status]: the initial statutes of the role
        """
        pass

    @abstractmethod
    def get_associated_phases(self) -> List[Phase]:
        """Return the phases that are associated with the role,
        i.e. the phases that have to play when the role is in the game.
        These phases will be removed of the game as soon as all players having a role that requires these phases are dead.

        Returns:
            List[Phase]: the associated phases
        """
        pass

    @classmethod
    @abstractmethod
    def get_textual_description(cls) -> str:
        """Return a textual description of the role. This will be given to the player having this role when the game starts.
        This should be clear and self-explanatory enough for a player to understand the role.
        This can be used by human players but also by AI agents to understand the role.

        Returns:
            str: a textual description of the role
        """
        pass

    @classmethod
    @abstractmethod
    def get_short_textual_description(cls) -> str:
        """A short description of the role (for other players to see)."""
        pass

    # ===== Methods for specific roles =====

    def initialize_role(self, state: State):
        """Apply any initialization of the role at the beginning of the game.
        This can have an effect of the role instance but also on the state of the game.

        Args:
            state (State): the current state of the game
        """
        pass

    def apply_death_announcement_and_confirm(
        self, state: State, id_player: int, cause: CauseOfDeath
    ) -> bool:
        """Apply any events supposed to happen due to that role if the player is announced dead.
        If the player is not supposed to die, return False.
        Else, return True (default).

        Args:
            state (State): the current state of the game
            id_player (int): the id of the player who died
            cause (CauseOfDeath): the cause of death of the player

        Returns:
            bool: whether the death is confirmed
        """
        return True

    def apply_death_consequences(
        self, state: State, id_player: int, cause: CauseOfDeath
    ):
        """Apply any events due to this role of the death of the player.
        By default, it does nothing.

        Args:
            state (State): the current state of the game
            id_player (int): the id of the player who died
            cause (CauseOfDeath): the cause of death of the player
        """
        pass

    # ===== Helper methods =====

    def __repr__(self):
        """By default, the representation of a role is its name as well as its initial faction."""
        return f"{self.get_name()} ({self.get_initial_faction()})"

    def __eq__(self, other: "RoleWW") -> bool:
        """By default, two roles are equal if they have the same name and the same id_player.
        This method can be overriden if needed.
        """
        return self.get_name() == other.get_name() and self.id_player == other.id_player

    def __hash__(self) -> int:
        return hash(self.get_name())

    def get_appearance_name(self) -> str:
        """Get the name of the role that should be displayed to informative actions from the other agents.
        By default, it is the same as the role name,
        but certain roles have the faculty to hide their true identity.
        """
        return self.get_name()

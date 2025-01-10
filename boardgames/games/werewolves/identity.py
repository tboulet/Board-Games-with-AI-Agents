from dataclasses import dataclass
from typing import List
from boardgames.games.werewolves.factions import FactionsWW, LIST_FACTIONS_BY_PRIORITY
from boardgames.games.werewolves.roles.base_role import RoleWW
from boardgames.games.werewolves.statutes.base_status import Status


@dataclass
class Identity:
    """An identity describes the game status of a player.
    It is composed of :
    - a role (RoleWW) that the player has and will determine its power and initial faction and statutes
    - a faction (FactionsWW) that the player belongs to (can change during the game) and with which the player wins
    - a list of statutes (List[Status]) that the player has and that can change during the game.
    Statutes are markers associated to the player that can determine how it interacts with the game.
    """

    role: RoleWW
    faction: FactionsWW
    statutes: List[Status]

    def __init__(self, role: RoleWW, id_player: int):
        self.role = role
        self.faction = self.role.get_initial_faction()
        self.statutes = self.role.get_initial_statutes()
        self.id_player = id_player
        self.role.set_id_player(id_player)
        
    def have_status(self, status: List[Status]) -> bool:
        """Return whether the player has the given status or not.

        Args:
            status (List[Status]): the status to check

        Returns:
            bool: whether the player has the status
        """
        return status in self.statutes

    def remove_status(self, status: str) -> None:
        """Try to remove the status from the player. If the status is not present, do nothing.

        Args:
            status (str): the status to remove
        """
        if status in self.statutes:
            self.statutes.remove(status)

    def add_status(self, status: str) -> None:
        """Add a status to the player.

        Args:
            status (str): the status to add to the player
        """
        self.statutes.append(status)

    def change_faction(self, faction: FactionsWW) -> None:
        """Change the faction of the player. Only change it if the new faction has higher or equal importance than the current one.

        Args:
            faction (FactionsWW): the new faction
        """
        current_faction_priority = LIST_FACTIONS_BY_PRIORITY.index(self.faction)
        new_faction_priority = LIST_FACTIONS_BY_PRIORITY.index(faction)
        if new_faction_priority <= current_faction_priority:
            self.faction = faction

    def __repr__(self):
        """The representation of an identity is its role name and its faction, as well as its status if any."""
        res = f"{self.role.get_name()} ({self.faction})"
        if len(self.statutes) > 0:
            res += f" Status:{self.statutes}"
        res = f"<{res}>"
        return res

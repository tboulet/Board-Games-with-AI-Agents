from dataclasses import dataclass
from typing import List
from boardgames.games.werewolves.factions import FactionsWW, LIST_FACTIONS_BY_PRIORITY
from boardgames.games.werewolves.roles.base_role import RoleWW
from boardgames.games.werewolves.statutes.base_status import Status


@dataclass
class Identity:
    """An identity describes the game status of a player. It is defined by a name, a faction, and a boolean indicating if it is a wolf or not."""

    role: RoleWW
    faction: FactionsWW
    statutes: List[Status]

    def __init__(self, role: RoleWW):
        self.role = role
        self.faction = self.role.get_initial_faction()
        self.statutes = self.role.get_initial_statutes()

    def have_status(self, status: List[Status]) -> bool:
        return status in self.statutes

    def remove_status(self, status: str) -> None:
        if status in self.statutes:
            self.statutes.remove(status)

    def add_status(self, status: str) -> None:
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
        res = f"{self.role.get_name()} ({self.faction})"
        if len(self.statutes) > 0:
            res += f" Status:{self.statutes}"
        res = f"<{res}>"
        return res

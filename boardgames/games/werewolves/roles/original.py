from typing import List
from boardgames.games.werewolves.factions import FactionsWW
from boardgames.games.werewolves.phase.base_phase import Phase
from boardgames.games.werewolves.state import StateWW
from boardgames.games.werewolves.roles.base_role import RoleWW
from boardgames.games.werewolves.statutes.base_status import Status
from boardgames.types import JointAction








class RoleSeer(RoleWW):
    @classmethod
    def get_name(cls) -> str:
        return "Seer"

    def get_initial_faction(self) -> FactionsWW:
        return FactionsWW.VILLAGE

    def get_initial_statutes(self) -> List[Status]:
        return []

    def get_associated_phases(self) -> List[str]:
        return [Phase.SEER_PHASE]

    def get_textual_description(self) -> str:
        return (
            "The seer is a villager with a special power. Each night, the seer can choose a player to see its role. The seer can use this information to help the villagers."
            "Your power are : \n"
            "- each night, you can choose a player to see its role."
        )


class RoleWitch(RoleWW):

    @classmethod
    def get_name(cls) -> str:
        return "Witch"

    def get_initial_faction(self) -> FactionsWW:
        return FactionsWW.VILLAGE

    def get_initial_statutes(self) -> List[Status]:
        return [Status.HAS_HEALING_POTION, Status.HAS_DEATH_POTION]

    def get_associated_phases(self) -> List[str]:
        return [Phase.WITCH_PHASE]

    def get_textual_description(self) -> str:
        return (
            "The witch is a villager with a special power. The witch has two potions : a potion of healing and a potion of death. The witch can use these potions to help the villagers."
            "She can use each potion only once during the game, and only one potion per night."
            "Your power are : \n"
            "- healing potion : you are noticed of the player attacked by the werewolves (if any). You can choose to heal this player, and he will survive the attack.\n"
            "- death potion : you can choose a player to eliminate. This player will be eliminated."
        )


class RoleHunter(RoleWW):

    @classmethod
    def get_name(cls) -> str:
        return "Hunter"

    def get_initial_faction(self) -> FactionsWW:
        return FactionsWW.VILLAGE

    def get_initial_statutes(self) -> List[Status]:
        return []

    def get_associated_phases(self) -> List[str]:
        return [Phase.HUNTER_CHOICE]

    def get_textual_description(self) -> str:
        return (
            "The hunter is a villager with a special power. The hunter can choose a player to eliminate when he dies."
            "Your power are : \n"
            "- when you die, you can choose a player to eliminate."
        )


class RoleThief(RoleWW):

    @classmethod
    def get_name(cls) -> str:
        return "Thief"

    def get_initial_faction(self) -> FactionsWW:
        return FactionsWW.THIEF

    def get_initial_statutes(self) -> List[Status]:
        return [Status.HAS_THIEF_POWER, Status.IS_SOLO]

    def get_associated_phases(self) -> List[str]:
        return [Phase.THIEF_PHASE]

    def get_textual_description(self) -> str:
        return (
            "The thief is a player that can steal the role of another player once he dies."
            "Your power are : \n"
            "- once per game, you can choose a player to steal his role when he dies. When he dies, you will become this role."
        )


ROLES_ORIGINAL = {
    RoleSeer.get_name(): RoleSeer,
    RoleWitch.get_name(): RoleWitch,
    RoleHunter.get_name(): RoleHunter,
    RoleThief.get_name(): RoleThief,
}

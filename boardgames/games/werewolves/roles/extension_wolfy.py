from typing import List
from boardgames.games.werewolves.factions import FactionsWW
from boardgames.games.werewolves.identity import Identity
from boardgames.games.werewolves.statutes.base_status import Status
from boardgames.games.werewolves.roles.base_role import RoleWW
from boardgames.games.werewolves.phase.base_phase import Phase


class RoleGravedigger(RoleWW):

    @classmethod
    def get_name(cls) -> str:
        return "Gravedigger"

    def get_initial_faction(self) -> FactionsWW:
        return FactionsWW.VILLAGE

    def get_initial_statutes(self) -> List[Status]:
        return []

    def get_associated_phases(self) -> List[str]:
        return [Phase.GRAVEDIGGER_CHOICE]

    def get_textual_description(self) -> str:
        return (
            "The gravedigger is a villager with a special power. At his death, he can choose a player. "
            "This player as well as another one will see their names publicly displayed, with the guarantee that one of them is a villager, and the other is not."
        )


class RoleRedRidingHood(RoleWW):

    @classmethod
    def get_name(cls) -> str:
        return "Red Riding Hood"

    def get_initial_faction(self) -> FactionsWW:
        return FactionsWW.VILLAGE

    def get_initial_statutes(self) -> List[Status]:
        return [Status.IS_PROTECTED_RED_HOOD]

    def get_associated_phases(self) -> List[str]:
        return []

    def get_textual_description(self) -> str:
        return (
            "Red Riding Hood is a villager that is protected from the wolves as long as the hunter is alive."
            "Your power are : \n"
            "- you are protected from the werewolves' attack as long as the hunter is alive."
        )


class RoleMercenary(RoleWW):

    @classmethod
    def get_name(cls) -> str:
        return "Mercenary"

    def get_initial_faction(self) -> FactionsWW:
        return FactionsWW.MERCENARY

    def get_initial_statutes(self) -> List[Status]:
        return [Status.IS_SOLO]

    def get_associated_phases(self) -> List[str]:
        return [Phase.VICTORY_CHECK, Phase.MERCENARY_CHECK]

    def get_textual_description(self) -> str:
        return "On the first vote, your aim is to kill your assigned target. If you succeed, you win the game instantly. If not, you become a villager"


class RoleNecromancer(RoleWW):

    @classmethod
    def get_name(cls) -> str:
        return "Necromancer"

    def get_initial_faction(self) -> FactionsWW:
        return FactionsWW.VILLAGE

    def get_initial_statutes(self) -> List[Status]:
        return []

    def get_associated_phases(self) -> List[str]:
        return [Phase.NECROMANCER_PHASE]

    def get_textual_description(self) -> str:
        return (
            "The necromancer is a villager that can speak with the deads."
            "Your power are : \n"
            "- each night, you can choose a player to speak with. You will be able to ask them questions and they will be able to answer."
        )


ROLES_EXTENSION_WOLFY = {
    RoleGravedigger.get_name(): RoleGravedigger,
    RoleRedRidingHood.get_name(): RoleRedRidingHood,
    RoleMercenary.get_name(): RoleMercenary,
    RoleNecromancer.get_name(): RoleNecromancer,
}

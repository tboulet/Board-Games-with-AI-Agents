from typing import List
from boardgames.games.werewolves.factions import FactionsWW
from boardgames.games.werewolves.roles.base_role import RoleWW
from boardgames.games.werewolves.phase.base_phase import Phase
from boardgames.games.werewolves.statutes.base_status import Status


class RoleAbominableSectarian(RoleWW):

    @classmethod
    def get_name(cls) -> str:
        return "Abominable Sectarian"

    def get_initial_faction(self) -> FactionsWW:
        return FactionsWW.ABOMINABLE_SECTARIAN

    def get_initial_statutes(self) -> List[Status]:
        return [Status.IS_SOLO]

    def get_associated_phases(self) -> List[str]:
        return [Phase.VICTORY_CHECK]

    def get_textual_description(self) -> str:
        return (
            "The Abominable Sectarian is an independent role. "
            "To win, he must succeed in eliminating all the players in the group opposite him, while remaining alive. "
            "The division of the village into two groups is made public and announced at the start of the game, "
            "but the village doesn't know which group the Abominable Sectarian is in."
        )


class RoleAngel(RoleWW):

    @classmethod
    def get_name(cls) -> str:
        return "Angel"

    def get_initial_faction(self) -> FactionsWW:
        return FactionsWW.ANGEL

    def get_initial_statutes(self) -> List[Status]:
        return []

    def get_associated_phases(self) -> List[str]:
        return [Phase.VICTORY_CHECK, Phase.ANGEL_CHECK]

    def get_textual_description(self) -> str:
        return (
            "The Angel is an independent role. "
            "To win, he must be voted by the first vote of the game. "
            "If he is voted, he wins the game. "
            "If not, he becomes a villager."
        )


class RoleWolfdog(RoleWW):

    @classmethod
    def get_name(cls) -> str:
        return "Wolfdog"

    def get_initial_faction(self) -> FactionsWW:
        return FactionsWW.VILLAGE

    def get_initial_statutes(self) -> List[Status]:
        return []

    def get_associated_phases(self) -> List[str]:
        return [Phase.WOLFDOG_CHOICE]

    def get_textual_description(self) -> str:
        return f"The Wolfdog is a role that can choose whether to be a Dog (villager) or a Wolf (werewolf) at the beginning of the game. "


class RoleWildChild(RoleWW):

    @classmethod
    def get_name(cls) -> str:
        return "Wild Child"

    def get_initial_faction(self) -> FactionsWW:
        return FactionsWW.VILLAGE

    def get_initial_statutes(self) -> List[Status]:
        return []

    def get_associated_phases(self) -> List[str]:
        return []

    def get_textual_description(self) -> str:
        return (
            "The Wild Child is a villager that will become a werewolf if his tutor dies. "
            "The tutor is chosen randomly among the members of the village. The Wild Child knows who his tutor is."
        )


class RoleJudge(RoleWW):

    ABSENT_NIGHT_INDICATOR = "<no night happened>"

    @classmethod
    def get_name(cls) -> str:
        return "Judge"

    def get_initial_faction(self) -> FactionsWW:
        return FactionsWW.VILLAGE

    def get_initial_statutes(self) -> List[Status]:
        return [Status.HAS_JUDGE_POWER]

    def get_associated_phases(self) -> List[str]:
        return [Phase.JUDGE_PHASE]

    def get_textual_description(self) -> str:
        return (
            "The Judge is a villager that once in the game can choose to create a second vote. "
            "He can choose this right after the first vote."
        )


class RoleBearShowman(RoleWW):

    @classmethod
    def get_name(cls) -> str:
        return "Bear Showman"

    def get_initial_faction(self) -> FactionsWW:
        return FactionsWW.VILLAGE

    def get_initial_statutes(self) -> List[Status]:
        return []

    def get_associated_phases(self) -> List[str]:
        return [Phase.BEAR_SHOWMAN_PHASE]

    def get_textual_description(self) -> str:
        return (
            "The Bear Showman is a villager possessing a passive power. "
            "Each night, it's bear will growl for as many wolves as there is next to him (including himself). "
            "The number of growls will increase by a random value in {-1, 0, 1}."
        )


class RoleFox(RoleWW):

    @classmethod
    def get_name(cls) -> str:
        return "Fox"

    def get_initial_faction(self) -> FactionsWW:
        return FactionsWW.VILLAGE

    def get_initial_statutes(self) -> List[Status]:
        return []

    def get_associated_phases(self) -> List[str]:
        return [Phase.FOX_PHASE]

    def get_textual_description(self) -> str:
        return (
            "The Fox is a villager possessing a deduction power. "
            "Each night, he can choose 3 players and will know if the group contains at least one wolf. "
            "If he find no wolf, he loses his power (to counter the huge information he can get)."
        )


class RoleVillagerVillager(RoleWW):

    @classmethod
    def get_name(cls) -> str:
        return "Villager Villager"

    def get_initial_faction(self) -> FactionsWW:
        return FactionsWW.VILLAGE

    def get_initial_statutes(self) -> List[Status]:
        return []

    def get_associated_phases(self) -> List[str]:
        return []

    def get_textual_description(self) -> str:
        return "The Villager Villager is a villager that is publicly revealed as a villager at the beginning of the game."


class RoleSister(RoleWW):

    @classmethod
    def get_name(cls) -> str:
        return "Sister"

    def get_initial_faction(self) -> FactionsWW:
        return FactionsWW.VILLAGE

    def get_initial_statutes(self) -> List[Status]:
        return []

    def get_associated_phases(self) -> List[str]:
        return [Phase.SISTER_SPEECH]

    def get_textual_description(self) -> str:
        return (
            "The Sister is a villager that knows the identity of the other Sister. "
            "They can send a message to the other Sister each night."
            "If one of the Sister dies, the other one will know of what cause of death she died."
        )


class RoleBlackWolf(RoleWW):

    @classmethod
    def get_name(cls) -> str:
        return "Black Wolf"

    def get_initial_faction(self) -> FactionsWW:
        return FactionsWW.WEREWOLVES

    def get_initial_statutes(self) -> List[Status]:
        return [Status.IS_WOLF, Status.HAS_INFECTION_POWER]

    def get_associated_phases(self) -> List[str]:
        return [Phase.INFECTION_PHASE]

    def get_textual_description(self) -> str:
        return (
            "The black wolf is a werewolf with a special power. The black wolf can infect a player once per game. The player will join the werewolves but keep all his powers."
            "Your power are : \n"
            "- each night, you can choose to play your one time infection power. "
        )


ROLES_EXTENSION_PERSONNAGES = {
    RoleAbominableSectarian.get_name(): RoleAbominableSectarian,
    RoleAngel.get_name(): RoleAngel,
    RoleWolfdog.get_name(): RoleWolfdog,
    RoleWildChild.get_name(): RoleWildChild,
    RoleJudge.get_name(): RoleJudge,
    RoleBearShowman.get_name(): RoleBearShowman,
    RoleFox.get_name(): RoleFox,
    RoleVillagerVillager.get_name(): RoleVillagerVillager,
    RoleSister.get_name(): RoleSister,
    RoleBlackWolf.get_name(): RoleBlackWolf,
}

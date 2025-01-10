from typing import List
from boardgames.games.werewolves.factions import FactionsWW
from boardgames.games.werewolves.identity import Identity
from boardgames.games.werewolves.statutes.base_status import Status
from boardgames.games.werewolves.roles.base_role import RoleWW
from boardgames.games.werewolves.phase.base_phase import Phase


class RoleSavior(RoleWW):
    @classmethod
    def get_name(cls) -> str:
        return "Savior"

    def get_initial_faction(cls) -> FactionsWW:
        return FactionsWW.VILLAGE

    def get_initial_statutes(self) -> List[Status]:
        return []

    def get_associated_phases(self) -> List[str]:
        return [Phase.SAVIOR_PHASE]

    @classmethod
    def get_textual_description(cls) -> str:
        return (
            "The savior is a villager with a special power. The savior can protect a player from the werewolves' attack."
            "Your power are : \n"
            "- each night, you can choose a player to protect. This player will survive the werewolves' attack if he is chosen by the werewolves."
        )


class RoleElder(RoleWW):

    @classmethod
    def get_name(cls) -> str:
        return "Elder"

    def get_initial_faction(cls) -> FactionsWW:
        return FactionsWW.VILLAGE

    def get_initial_statutes(self) -> List[Status]:
        return [Status.IS_PROTECTED_ELDER]

    def get_associated_phases(self) -> List[str]:
        return []

    @classmethod
    def get_textual_description(cls) -> str:
        return (
            "The elder is a villager with a special power. The elder is protected from one of the werewolves' attack."
            "Your power are : \n"
            "- you are protected from the first werewolves' attack."
        )


class RoleVillageFool(RoleWW):

    @classmethod
    def get_name(cls) -> str:
        return "Village Fool"

    def get_initial_faction(cls) -> FactionsWW:
        return FactionsWW.VILLAGE

    def get_initial_statutes(self) -> List[Status]:
        return [Status.IS_PROTECTED_VILLAGE_FOOL]

    def get_associated_phases(self) -> List[str]:
        return []

    @classmethod
    def get_textual_description(cls) -> str:
        return (
            "The village fool is a player that does not die if he is eliminated by the village (the first time)."
            "Instead, he is publicly revealed as the village fool and can not vote anymore."
        )


ROLES_EXTENSION_NEW_MOON = {
    RoleElder.get_name(): RoleElder,
    RoleSavior.get_name(): RoleSavior,
    RoleVillageFool.get_name(): RoleVillageFool,
}

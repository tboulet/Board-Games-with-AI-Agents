import random
import re
from typing import Dict, List
from boardgames.games.werewolves.causes_of_deaths.base_cause import CauseOfDeath
from boardgames.games.werewolves.factions import FactionsWW
from boardgames.games.werewolves.identity import Identity
from boardgames.games.werewolves.statutes.base_status import Status
from boardgames.games.werewolves.roles.base_role import RoleWW
from boardgames.games.werewolves.phase.base_phase import Phase


class RoleInvisible(RoleWW):

    def __init__(self):
        assert (
            Status.IS_INVISIBLE in self.get_initial_statutes()
        ), "An invisible role should have the status IS_INVISIBLE"
        assert (
            Phase.INVISIBLE_PHASE in self.get_associated_phases()
        ), "An invisible role should have the phase INVISIBLE_PHASE"
        super().__init__()

    @classmethod
    def get_textual_description(cls) -> str:
        return (
            f"You are the role {self}. You win with the faction {self.get_initial_faction()}. \n\n"
            "As an invisible role, you have the following caracteristics : \n"
            "- each night, you can decide to perform an 'Invisble Attack' on a player. "
            "If this player is an Invisible Role, it will kill them, otherwise, you will die by failing your attack. \n"
            "- you can be targeted by Invisible Attacks and die this way. \n"
            "- you are immune to any other type of attack at night. \n"
            "- you have additional power that depends of your role (see next section) \n\n"
            "The specific powers are the following : \n"
            "Little Girl : you can see certain words of the werewolves' discussion (you don't see the names of the wolves) \n"
            "Perfidious Wolf : if you kill the Little Girl, you win an additional attack per night for the rest of the game, which makes you a very dangerous enemy. \n"
            "Spirit : you win by killing both the Little Girl and the Perfious Wolf. If they are killed by other means, you instantly die and lose the game. \n"
        )

    def get_associated_cause_of_death(self) -> CauseOfDeath:
        if self.get_name() == "Little Girl":
            return CauseOfDeath.INVISIBLE_ATTACK_LITTLE_GIRL
        elif self.get_name() == "Perfidious Wolf":
            return CAUSES_OF_DEATH.INVISIBLE_ATTACK_PERFIDIOUS_WOLF
        elif self.get_name() == "Spirit":
            return CAUSES_OF_DEATH.INVISIBLE_ATTACK_SPIRIT
        else:
            raise ValueError(
                f"Role {self.get_name()} is not an invisible role with a specific cause of death."
            )


class RoleLittleGirl(RoleInvisible):

    @classmethod
    def get_name(cls) -> str:
        return "Little Girl"

    def get_initial_faction(cls) -> FactionsWW:
        return FactionsWW.VILLAGE

    def get_initial_statutes(self) -> List[Status]:
        return [Status.IS_INVISIBLE]

    def get_associated_phases(self) -> List[str]:
        return [Phase.INVISIBLE_PHASE]

    def partially_hide_message(self, message: str, config_little_girl: Dict) -> str:
        """
        Transform the message to hide certain words based on the given configuration.

        Args:
            message (str): The message to transform.
            config_little_girl (Dict): The configuration of the transformation.

        Returns:
            str: The transformed message.
        """
        words = message.split()
        transformed_words = []

        # Handle the "cant_see_numbers" configuration
        if config_little_girl["cant_see_numbers"]:
            words = [re.sub(r"\d", "*", word) for word in words]

        # Handle the "proportion_hidden_words" configuration
        proportion = config_little_girl["proportion_hidden_words"]
        num_hidden_words = int(len(words) * proportion)
        hidden_indices = random.sample(range(len(words)), num_hidden_words)

        for i, word in enumerate(words):
            if i in hidden_indices:
                transformed_words.append("*" * len(word))
            else:
                transformed_words.append(word)

        return " ".join(transformed_words)


class RolePerfidiousWolf(RoleInvisible):

    @classmethod
    def get_name(cls) -> str:
        return "Perfidious Wolf"

    def get_initial_faction(cls) -> FactionsWW:
        return FactionsWW.WEREWOLVES

    def get_initial_statutes(self) -> List[Status]:
        return [Status.IS_INVISIBLE]

    def get_associated_phases(self) -> List[str]:
        return [
            Phase.INVISIBLE_PHASE,
            Phase.NIGHT_WOLF_SPEECH,
            Phase.NIGHT_WOLF_VOTE,
            Phase.PERFIDIOUS_WOLF_ATTACK,
        ]


class RoleSpirit(RoleInvisible):

    def __init__(self):
        self.n_roles_invisible_found = 0
        super().__init__()

    @classmethod
    def get_name(cls) -> str:
        return "Spirit"

    def get_initial_faction(cls) -> FactionsWW:
        return FactionsWW.SPIRIT

    def get_initial_statutes(self) -> List[Status]:
        return [Status.IS_INVISIBLE, Status.IS_SOLO]

    def get_associated_phases(self) -> List[str]:
        return [Phase.INVISIBLE_PHASE, Phase.VICTORY_CHECK]


ROLES_EXTENSION_INVISIBLES = {
    RoleLittleGirl.get_name(): RoleLittleGirl,
    RolePerfidiousWolf.get_name(): RolePerfidiousWolf,
    RoleSpirit.get_name(): RoleSpirit,
}

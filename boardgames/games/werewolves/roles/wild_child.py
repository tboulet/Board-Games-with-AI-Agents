from collections import defaultdict
import random
from typing import List, Tuple
from boardgames.games.werewolves.causes_of_deaths.base_cause import CauseOfDeath
from boardgames.games.werewolves.factions import FactionsWW
from boardgames.games.werewolves.phase.base_phase import Phase
from boardgames.games.werewolves.roles.base_role import RoleWW
from boardgames.games.werewolves.state import StateWW, StatusIsWolf
from boardgames.games.werewolves.statutes.base_status import Status
from boardgames.types import JointAction
from boardgames.action_spaces import (
    FiniteActionSpace,
    JointActionSpace,
    TextualActionSpace,
)
from boardgames.types import (
    InfoDict,
    JointAction,
    JointObservation,
    JointPlayingInformation,
    JointReward,
    State,
    TerminalSignal,
)


class StatusModelWildChild(Status):
    
    def __init__(self, id_wild_child: int):
        self.id_wild_child = id_wild_child
        
    def get_name(self) -> str:
        return "Model Wild Child"
    
    def apply_death_consequences(self, state : StateWW, id_player: int, cause: CauseOfDeath):
        # If the model is eliminated, the Wild Child switches sides
        state.common_obs.log(
            f"[!] Wild Child {self.id_wild_child}'s model was eliminated.",
            "INFO",
        )
        state.turn_player_into_wolf(self.id_wild_child)


class RoleWildChild(RoleWW):

    @classmethod
    def get_name(cls) -> str:
        return "Wild Child"

    @classmethod
    def get_initial_faction(cls) -> FactionsWW:
        return FactionsWW.VILLAGE

    def get_initial_statutes(self) -> List[Status]:
        return []

    def get_associated_phases(self) -> List[Phase]:
        return []

    @classmethod
    def get_textual_description(cls) -> str:
        return (
            "Role: Wild Child. Your objective is initially to help the Villagers eliminate all the Werewolves. "
            "At the start of the game, you secretly choose a 'role model' among the other players. If your chosen role model is eliminated at any point in the game, "
            "you will immediately switch sides and join the Werewolves, adopting their goal to eliminate all Villagers. "
            "Until your role model is eliminated, you behave as a normal Villager, trying to stay undetected and participating in discussions and voting. "
            "Winning Condition: "
            "- If your role model survives and all Werewolves are eliminated, you win with the Villagers. "
            "- If your role model is eliminated, you switch allegiance and win if the Werewolves eliminate all Villagers. "
            "Strategic Tips: "
            "- Choose your role model wisely; selecting a strong or well-protected player can increase your chances of staying with the Villagers. "
            "- If your role model is eliminated, you must quickly adapt your strategy to work against the Villagers without raising suspicion. "
            "- Avoid drawing attention to your special role early in the game to prevent being targeted by the Werewolves or Villagers. "
            "- If you transition to the Werewolves, be discreet in shifting your behavior to avoid being suspected. "
            "Choose carefully, adapt to the changing dynamics, and maximize your chances of winning."
        )

    @classmethod
    def get_short_textual_description(cls):
        return "Initially a Villager, transforms into a Werewolf if their randomly chosen model is eliminated."

    def initialize_role(self, state: StateWW):
        id_player_model = random.choice(
            [i for i in range(state.n_players) if i != self.id_player]
        )
        state.identities[id_player_model].add_status(StatusModelWildChild(id_wild_child=self.id_player))
        state.common_obs.log(
            f"[!] Wild Child {self.id_player} was assigned player {id_player_model} as a model.",
            "INFO",
        )
        state.common_obs.add_message(
            f"Your model was chosen to be player {id_player_model}.",
            idx_player=self.id_player,
        )

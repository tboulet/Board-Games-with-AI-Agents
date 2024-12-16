from abc import ABC, abstractmethod
from enum import Enum
import random
from typing import Dict, List, Optional, Tuple, Union
import numpy as np
from boardgames.action_spaces import FiniteActionSpace
from boardgames.games.base_game import BaseGame
from boardgames.games.base_text_game import BaseTextBasedGame
from boardgames.types import Observation, Action, State, AgentID
from boardgames.games.utils import CommonObs
from boardgames.utils import str_to_literal
from boardgames.action_spaces import ActionsSpace


class RoleTimesBomb(str, Enum):
    DEFUSER = "defuser"
    GANGSTER = "Gangster"

    def __repr__(self):
        return self.value


class CardTimesBomb(str, Enum):
    SAFE = "Safe"
    DEFUSE = "Defuse"
    BOMB = "Bomb"

    def __repr__(self):
        return self.value


class PhaseTimesBomb(str, Enum):
    ANNOUNCEMENT = "Announcement"
    CUT = "Cut"


class StateTimesBomb(State):

    def __init__(
        self,
        n_players: int,
        game: BaseGame,
        n_cards_per_player: int = 5,
        n_bombs: int = 1,
        n_required_bombs: int = 1,
        n_diffuses: int = None,
        n_required_diffuses: int = None,
        do_force_truth_for_defusers: bool = False,
        do_allow_1_card_round: bool = False,
        do_allow_inverse_cut: bool = False,
        **kwargs,
    ) -> None:
        # Initialize game variables
        self.n_players = n_players
        self.game = game
        self.n_cards_per_player = n_cards_per_player
        self.n_cards_revealed_this_round = 0
        self.n_bombs = n_bombs
        self.n_required_bombs = n_required_bombs
        assert (
            self.n_required_bombs <= self.n_bombs
        ), "n_required_bombs must be less than or equal to n_bombs"
        self.n_found_bombs = 0
        self.n_defuses = n_diffuses if n_diffuses is not None else self.n_players
        self.n_required_diffuse = (
            n_required_diffuses if n_required_diffuses is not None else self.n_defuses
        )
        assert (
            self.n_required_diffuse <= self.n_defuses
        ), "n_required_diffuse must be less than or equal to n_diffuse"
        self.force_truth_for_defusers = do_force_truth_for_defusers
        self.n_found_defuse = 0
        self.n_neutral_cards = (
            self.n_players * self.n_cards_per_player - self.n_bombs - self.n_defuses
        )
        self.do_allow_1_card_round = do_allow_1_card_round
        self.do_allow_inverse_cut = do_allow_inverse_cut
        self.list_is_playing_defusers: List[bool] = None
        self.previous_player_cutter: int = None
        self.done: bool = False
        self.config = kwargs
        # Initialize random variables
        if 5 <= self.n_players <= 6:
            n_gangsters = 2
        elif self.n_players == 7:
            n_gangsters = random.choice([2, 3])  # 2 or 3 gangsters randomly
        elif self.n_players == 8:
            n_gangsters = 3
        else:
            raise ValueError(f"n_players={self.n_players} not supported.")
        self.roles: List[RoleTimesBomb] = [RoleTimesBomb.DEFUSER] * (
            self.n_players - n_gangsters
        ) + [RoleTimesBomb.GANGSTER] * n_gangsters
        random.shuffle(self.roles)
        self.deck: List[CardTimesBomb] = (
            [CardTimesBomb.SAFE] * self.n_neutral_cards
            + [CardTimesBomb.DEFUSE] * self.n_defuses
            + [CardTimesBomb.BOMB] * self.n_bombs
        )
        random.shuffle(self.deck)
        self.cards_revealed: List[CardTimesBomb] = []
        self.hands: List[List[CardTimesBomb]] = None
        self.hands_revealed: List[List[CardTimesBomb]] = None

    def reset(self) -> Tuple[
        State,
        List[bool],
        List[Observation],
        List[ActionsSpace],
        Dict,
    ]:
        # Initialize common observation
        self.common_obs: CommonObs = CommonObs(n_players=self.n_players)
        self.common_obs.add_global_message("The game has started.")
        self.common_obs.add_global_message(
            f"Table is composed of {self.n_players} players among which {self.roles.count(RoleTimesBomb.DEFUSER)} defusers and {self.roles.count(RoleTimesBomb.GANGSTER)} gangsters."
        )

        # Determine randomly starting player
        self.player_cutter: int = random.randint(0, self.n_players - 1)
        self.common_obs.add_global_message(f"The first cutter is {self.player_cutter}.")

        # Distribute roles and cards
        self.hands = [[] for _ in range(self.n_players)]
        for i in range(self.n_players):
            for _ in range(self.n_cards_per_player):
                self.hands[i].append(self.deck.pop())
            self.common_obs.add_message(
                f"You are at seet {i}. You get assigned the role {self.roles[i]}.", i
            )
        assert len(self.deck) == 0, "Deck should be empty after distributing cards."
        self.hands_revealed = [[] for _ in range(self.n_players)]

        # Start first round
        (
            rewards,
            next_state,
            self.list_is_playing_defusers,
            list_obs,
            list_action_spaces,
            done,
            info,
        ) = self.start_new_round()
        return (
            next_state,
            self.list_is_playing_defusers,
            list_obs,
            list_action_spaces,
            info,
        )

    def start_new_cut(self) -> Tuple[
        State,
        List[bool],
        List[Observation],
        List[ActionsSpace],
        Dict,
    ]:
        self.game_phase = PhaseTimesBomb.CUT
        action_available_for_cutter = []
        for idx_player in range(self.n_players):
            if idx_player == self.player_cutter:  # The cutter cannot cut his own wire
                continue
            if (
                idx_player == self.previous_player_cutter
                and not self.do_allow_inverse_cut
            ):  # The cutter cannot cut the wire of the previous cutter
                continue
            if (
                len(self.hands[idx_player]) == 0
            ):  # The cutter cannot cut the wire of a player with no cards
                continue
            action_available_for_cutter.append(str(idx_player))
        action_spaces_for_cutter = FiniteActionSpace(
            actions=action_available_for_cutter
        )
        list_action_spaces = self.game.empty_list_except(
            self.player_cutter, action_spaces_for_cutter
        )
        self.common_obs.add_global_message(
            f"Player {self.player_cutter} becomes the cutter. He must now pick a player among {action_available_for_cutter} to cut a wire."
        )
        self.common_obs.add_message(
            f"You must pick a player from which to cut a wire.", self.player_cutter
        )
        rewards = [0 for _ in range(self.n_players)]
        self.list_is_playing_defusers = self.game.empty_list_except(
            idx=self.player_cutter, value=True, fill=False
        )
        list_obs = self.game.empty_list_except(
            idx=self.player_cutter,
            value=self.common_obs[self.player_cutter],
            fill=False,
        )
        return (
            rewards,
            self,
            self.list_is_playing_defusers,
            list_obs,
            list_action_spaces,
            False,
            {},
        )

    def start_new_round(self) -> Tuple[
        List[float],
        State,
        List[bool],
        List[Observation],
        List[ActionsSpace],
        bool,
        Dict,
    ]:
        # Start a new round
        self.common_obs.add_global_message(
            f"Starting {self.n_cards_per_player}-cards-per-player round. Unrevealed cards are reshuffled and redistributed equally. There is {self.n_bombs-self.n_found_bombs} bomb and {self.n_defuses-self.n_found_defuse} defusing wires among the {sum([len(hand) for hand in self.hands])} unrevealed cards."
        )
        self.previous_player_cutter = None

        # Put hands back in the deck, shuffle it and redistribute cards
        self.deck = sum(self.hands, [])
        random.shuffle(self.deck)
        self.hands = [[] for _ in range(self.n_players)]
        for i in range(self.n_players):
            for _ in range(self.n_cards_per_player):
                self.hands[i].append(self.deck.pop())
            self.common_obs.add_message(
                f"You obtain the following cards : {self.hands[i]}", i
            )
        assert len(self.deck) == 0, "Deck should be empty after redistributing cards."
        self.hands_revealed = [[] for _ in range(self.n_players)]

        # Entering announcement phase
        self.game_phase: PhaseTimesBomb = PhaseTimesBomb.ANNOUNCEMENT
        rewards = [0 for _ in range(self.n_players)]
        self.common_obs.add_global_message(
            "The game is now in the announcement phase. You must claim the number of bombs and diffuse wires you have in the following format : (bomb, diffuse)."
        )
        self.announcement: List[bool] = [None for _ in range(self.n_players)]
        self.list_is_playing_defusers = [True for _ in range(self.n_players)]
        list_obs = [self.common_obs[i] for i in range(self.n_players)]
        actions_available: List[str] = []
        for n_b in range(
            0, min(self.n_bombs - self.n_found_bombs + 1, self.n_cards_per_player + 1)
        ):
            for n_d in range(
                0,
                min(
                    self.n_defuses - self.n_found_defuse + 1,
                    self.n_cards_per_player - n_b + 1,
                ),
            ):
                actions_available.append(str((n_b, n_d)))
        list_actions_available = [actions_available for _ in range(self.n_players)]
        if self.force_truth_for_defusers:
            for i in range(self.n_players):
                if self.roles[i] == RoleTimesBomb.DEFUSER:
                    list_actions_available[i] = [
                        str(
                            (
                                self.hands[i].count(CardTimesBomb.BOMB),
                                self.hands[i].count(CardTimesBomb.DEFUSE),
                            )
                        )
                    ]
        list_action_spaces = [
            FiniteActionSpace(actions=actions) for actions in list_actions_available
        ]

        # Return
        return (
            rewards,
            self,
            self.list_is_playing_defusers,
            list_obs,
            list_action_spaces,
            False,
            {},
        )

    def step(self, list_actions: List[Action]) -> Tuple[
        List[float],
        State,
        List[bool],
        List[Observation],
        List[ActionsSpace],
        bool,
        Dict,
    ]:
        # Annoucement phase
        if self.game_phase == PhaseTimesBomb.ANNOUNCEMENT:
            # Annouce the number of bombs and diffuse wires
            self.common_obs.reset_global()
            for idx_player, action in enumerate(list_actions):
                n_b, n_d = str_to_literal(action)
                self.announcement[idx_player] = (n_b, n_d)
            self.create_announcement_message()
            # Call the next phase
            return self.start_new_cut()

        # Cut phase
        elif self.game_phase == PhaseTimesBomb.CUT:
            # Cut a wire
            self.common_obs.reset(self.player_cutter)
            idx_player_cut_str = list_actions[self.player_cutter]
            idx_player_cut = str_to_literal(idx_player_cut_str)
            assert isinstance(idx_player_cut, int) and 0 <= idx_player_cut < self.n_players, f"Invalid player index : {idx_player_cut}"
            card_cut = self.hands[idx_player_cut].pop()
            self.previous_player_cutter = self.player_cutter
            self.cards_revealed.append(card_cut)
            self.hands_revealed[idx_player_cut].append(card_cut)
            # Apply the effect of the cut
            if card_cut == CardTimesBomb.BOMB:
                self.n_found_bombs += 1
                if self.n_required_bombs == 1:
                    self.common_obs.add_global_message(
                        f"Player {self.player_cutter} cut the wire of player {idx_player_cut} and found a bomb. Gangsters win."
                    )
                    return self.get_final_return(roles_win=[RoleTimesBomb.GANGSTER])
                elif self.n_found_bombs >= self.n_required_bombs:
                    self.common_obs.add_global_message(
                        f"Player {self.player_cutter} cut the wire of player {idx_player_cut} and found a bomb. ({self.n_found_bombs}/{self.n_required_bombs}). All bombs have been found. Gangsters win..."
                    )
                    return self.get_final_return(roles_win=[RoleTimesBomb.GANGSTER])
                else:
                    self.common_obs.add_global_message(
                        f"Player {self.player_cutter} cut the wire of player {idx_player_cut} and found a bomb. ({self.n_found_bombs}/{self.n_required_bombs})"
                    )
            elif card_cut == CardTimesBomb.DEFUSE:
                self.n_found_defuse += 1
                if self.n_found_defuse >= self.n_required_diffuse:
                    self.common_obs.add_global_message(
                        f"Player {self.player_cutter} cut the wire of player {idx_player_cut} and found a defusing wire. ({self.n_found_defuse}/{self.n_required_diffuse}). All defusing wires have been found. defusers win!"
                    )
                    return self.get_final_return(roles_win=[RoleTimesBomb.DEFUSER])
                else:
                    self.common_obs.add_global_message(
                        f"Player {self.player_cutter} cut the wire of player {idx_player_cut} and found a defusing wire. ({self.n_found_defuse}/{self.n_required_diffuse})"
                    )
            elif card_cut == CardTimesBomb.SAFE:
                self.common_obs.add_global_message(
                    f"Player {self.player_cutter} cut the wire of player {idx_player_cut} and found a safe wire. No effect."
                )

            else:
                raise ValueError(f"Unknown card : {card_cut}")

            # Update the announcement
            self.create_announcement_message()

            # Player cutter becomes the player cut
            self.player_cutter = idx_player_cut

            # Check if n_players cards have been revealed
            self.n_cards_revealed_this_round += 1
            if self.n_cards_revealed_this_round >= self.n_players:
                self.n_cards_revealed_this_round = 0
                self.n_cards_per_player -= 1
                # Check 1-card-per-player reach gangsters win criteria
                if self.n_cards_per_player == 1 and not self.do_allow_1_card_round:
                    self.common_obs.add_global_message(
                        "2-card-per-player round is over but defusers have not found all defusing wires. Gangsters win."
                    )
                    return self.get_final_return(roles_win=[RoleTimesBomb.GANGSTER])
                elif self.n_cards_per_player == 0:
                    raise ValueError(
                        "All cards have been revealed without the game stopping."
                    )

                # Start a new round
                return self.start_new_round()

            else:
                # Continue the cut phase
                return self.start_new_cut()

        else:
            raise ValueError(f"Unknown game phase : {self.game_phase}")

    def create_announcement_message(self) -> str:
        for idx_player, (n_b, n_d) in enumerate(self.announcement):
            visual_announcement = (
                ["B?"] * n_b
                + ["D?"] * n_d
                + ["--"] * (self.n_cards_per_player - n_b - n_d)
            )
            visual_announcement = "[" + " ".join(visual_announcement) + "]"
            if len(self.hands_revealed[idx_player]) > 0:
                n_b_revealed = self.hands_revealed[idx_player].count(CardTimesBomb.BOMB)
                n_d_revealed = self.hands_revealed[idx_player].count(
                    CardTimesBomb.DEFUSE
                )
                n_neutral_revealed = self.hands_revealed[idx_player].count(
                    CardTimesBomb.SAFE
                )
                visual_announcement_reveal = (
                    ["B"] * n_b_revealed
                    + ["D"] * n_d_revealed
                    + ["--"] * n_neutral_revealed
                )
                visual_announcement += (
                    f" (revealed : {'[' + ' '.join(visual_announcement_reveal) + '])'}"
                )
            self.common_obs.add_global_message(
                f"Player {idx_player} announced : {n_b} bomb and {n_d} diffuse wires. {visual_announcement}",
            )

    def get_final_return(self, roles_win: List[RoleTimesBomb]) -> Tuple[
        List[float],
        State,
        List[bool],
        List[Observation],
        List[ActionsSpace],
        bool,
        Dict,
    ]:
        rewards = [1 if role in roles_win else -1 for role in self.roles]
        self.common_obs.add_global_message(
            f"The game is over. Roles were : {self.roles}. Remains of hands were : {self.hands}."
        )
        self.done = True
        return (
            rewards,
            self,
            [False for _ in range(self.n_players)],
            self.common_obs,
            [None for _ in range(self.n_players)],
            True,
            {},
        )


class TimesBomb(BaseTextBasedGame):

    def __init__(
        self,
        n_players: int,
        **kwargs,
    ) -> None:
        self.n_players = n_players
        self.config = kwargs

    def get_game_context(self) -> str:
        context = f"""
You will play a game of TimesBomb. The game is composed of a table of {self.n_players} players among which some are defusers and some are gangsters. 
For the defusers to win, they must reveal the {self.n_players} defusing wires in 5 round or less and avoid at all price to reveal the bomb which will make the gangsters win instantly.
For the gangsters to win, they must reveal the bomb or prevent the defusers from revealing all defusing wires.

The game contains {self.n_players * 5} cards among which there is 1 bomb, {self.n_players} defusing wires and the rest ({self.n_players * 5 - self.n_players - 1}) are safe wires.
The game is played in rounds, starting with the 5-cards-per-player round, and ending with the 1-card-per-player round.
At the start of each round, the cards are reshuffled and redistributed among the players.
A round is composed of two phases : the announcement phase and the cut phase.
In the announcement phase, each player must claims the number of bomb (0 or 1 because there is only one fatal bomb) and defusing wires he has in his hand. defusers are forced to tell the truth, while gangsters can lie.
In the cut phase, the player who is the cutter must cut the wire of another player. The player whose wire is cut must reveal the wire cut. 
If it is a bomb, the gangsters win. If it is a defusing wire, the defusers are one step closer to winning. If it is a safe wire, nothing happens.
The player that got cut becomes the cutter for the next cut.
The round ends when {self.n_players} wires have been cut. Then cards are reshuffled and distributed randomly and a new round (with one less card per player) starts.

If you are a defuser, you should try to identify which player you can trust based on their announcement and the probabilities. You should avoid the bomb at all cost.
If you are a gangster, you should try to both deceive the defusers so that they trust you, and to discretely eventually search for the bomb and sabotage their efforts to find the defusing wires.
  
You are playing a textual board game. Your outputs must conform to the following rules:
1. Your **reasoning** should explain your thought process in natural language.
2. Your **action** must be a valid action among those specified in the list of available actions.
   
Always separate your reasoning from your action. Your final output should explicitly label "Reasoning" and "Action," and the action must appear on a new line.
Example:
Reasoning:
"I chose this action because..."
Action:
<your action>

Good luck!
        """
        return context

    def reset(
        self,
    ) -> Tuple[State, List[bool], List[Observation], List[ActionsSpace], Dict]:
        state = StateTimesBomb(n_players=self.n_players, game=self, **self.config)
        return state.reset()

    def step(self, state: State, list_actions: List[Action]) -> Tuple[
        List[float],
        State,
        List[bool],
        List[Observation],
        List[ActionsSpace],
        bool,
        Dict,
    ]:
        return state.step(list_actions)

    def get_n_players(self) -> int:
        """Return the number of players in the game.

        Returns:
            int: the number of players
        """
        return self.n_players

    def render(self, state: StateTimesBomb) -> None:
        """Render the current state of the game.

        Args:
            state (State): the current state of the game
        """
        if self.config["print_common_obs"]:
            print(state.common_obs)

        if self.config["print_obs"]:
            if state.done:
                print(f"The game is over. : {state.common_obs}")
            else:
                for i in range(self.n_players):
                    if state.list_is_playing_defusers[i]:
                        print(f"\n>>> Player {i} is playing :")
                        print(f"{state.common_obs[i]}")
                        if self.config["pause_at_each_obs_print"]:
                            input()

from abc import ABC, abstractmethod
from enum import Enum
import random
from typing import Dict, List, Optional, Tuple, Union
import numpy as np
from boardgames.games.base_game import BaseGame
from boardgames.types import Observation, Action, ActionsAvailable, State, AgentID
from boardgames.games.utils import CommonObs


class RoleTimesBomb(str, Enum):
    AGENT = "Agent"
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

    def __repr__(self):
        return self.value


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
        self.n_found_defuse = 0
        self.n_neutral_cards = (
            self.n_players * self.n_cards_per_player - self.n_bombs - self.n_defuses
        )
        self.do_allow_1_card_round = do_allow_1_card_round
        self.do_allow_inverse_cut = do_allow_inverse_cut
        self.list_is_playing_agents: List[bool] = (None,)
        self.previous_player_cutter: int = None
        self.done: bool = False
        self.config = kwargs
        # Initialize random variables
        if self.n_players == 5:
            self.roles: List[RoleTimesBomb] = [
                RoleTimesBomb.AGENT,
                RoleTimesBomb.AGENT,
                RoleTimesBomb.AGENT,
                RoleTimesBomb.GANGSTER,
                RoleTimesBomb.GANGSTER,
            ]
        else:
            raise ValueError(f"n_players={self.n_players} not supported.")
        random.shuffle(self.roles)
        self.deck: List[CardTimesBomb] = (
            [CardTimesBomb.SAFE] * self.n_neutral_cards
            + [CardTimesBomb.DEFUSE] * self.n_defuses
            + [CardTimesBomb.BOMB] * self.n_bombs
        )
        random.shuffle(self.deck)
        self.cards_revealed: List[CardTimesBomb] = []
        self.hands: List[List[CardTimesBomb]] = None

    def reset(self) -> Tuple[
        State,
        List[bool],
        List[Observation],
        List[ActionsAvailable],
        Dict,
    ]:
        # Initialize common observation
        self.common_obs: CommonObs = CommonObs(n_players=self.n_players)
        self.common_obs.add_global_message("The game has started.")
        
        # Determine randomly starting player
        self.player_cutter: int = random.randint(0, self.n_players - 1)
        self.common_obs.add_global_message(f"The first cutter is {self.player_cutter}.")
        
        # Distribute roles and cards
        self.hands = [[] for _ in range(self.n_players)]
        for i in range(self.n_players):
            for _ in range(self.n_cards_per_player):
                self.hands[i].append(self.deck.pop())
            self.common_obs.add_message(f"You are at seet {i}. You get assigned the role {self.roles[i]}.", i)
        assert len(self.deck) == 0, "Deck should be empty after distributing cards."
        
        # Start first round
        rewards, next_state, list_is_playing_agents, list_obs, list_actions_available, done, info = self.start_new_round()
        return next_state, list_is_playing_agents, list_obs, list_actions_available, info
    
    def start_new_cut(self) -> Tuple[
        State,
        List[bool],
        List[Observation],
        List[ActionsAvailable],
        Dict,
    ]:
        self.game_phase = PhaseTimesBomb.CUT
        rewards = [0 for _ in range(self.n_players)]
        list_is_playing_agents = self.game.empty_list_except(
            idx=self.player_cutter, value=True, fill=False
        )
        list_obs = self.game.empty_list_except(
            idx=self.player_cutter,
            value=self.common_obs[self.player_cutter],
            fill=False,
        )
        actions_available_for_cutter = []
        for idx_player in range(self.n_players):
            if (
                idx_player == self.player_cutter
            ):  # The cutter cannot cut his own wire
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
            actions_available_for_cutter.append(idx_player)
        list_actions_available = self.game.empty_list_except(
            self.player_cutter, actions_available_for_cutter
        )
        self.common_obs.add_global_message(
            f"Player {self.player_cutter} becomes the cutter. He must now pick a player among {actions_available_for_cutter} to cut a wire."
        )
        self.common_obs.add_message(
            f"You must pick a player from which to cut a wire.", self.player_cutter
        )
        return (
            rewards,
            self,
            list_is_playing_agents,
            list_obs,
            list_actions_available,
            False,
            {},
            )
            
    def start_new_round(self) -> Tuple[
        List[float],
        State,
        List[bool],
        List[Observation],
        List[ActionsAvailable],
        bool,
        Dict,
    ]:
        # Start a new round
        self.common_obs.add_global_message(
            f"Starting {self.n_cards_per_player}-cards-per-player round. Unrevealed cards are reshuffled and redistributed equally."
        )
        self.previous_player_cutter = None

        # Put hands back in the deck, shuffle it and redistribute cards
        self.deck = sum(self.hands, [])
        self.hands = [[] for _ in range(self.n_players)]
        for i in range(self.n_players):
            for _ in range(self.n_cards_per_player):
                self.hands[i].append(self.deck.pop())
            self.common_obs.add_message(f"You obtain the following cards : {self.hands[i]}", i)
        assert len(self.deck) == 0, "Deck should be empty after redistributing cards."
        
        # Entering announcement phase
        self.game_phase: PhaseTimesBomb = PhaseTimesBomb.ANNOUNCEMENT
        rewards = [0 for _ in range(self.n_players)]
        self.common_obs.add_global_message(
            "The game is now in the announcement phase. You must announce the number of bombs and diffuse wires you have (you can lie) in the following format : (bombs, diffuse)."
        )
        self.announcement: List[bool] = [None for _ in range(self.n_players)]
        self.list_is_playing_agents = [True for _ in range(self.n_players)]
        list_obs = [self.common_obs[i] for i in range(self.n_players)]
        actions_available: ActionsAvailable = []
        for n_b in range(0, min(self.n_bombs - self.n_found_bombs + 1, self.n_cards_per_player + 1)):
            for n_d in range(
                0, min(self.n_defuses - self.n_found_defuse + 1, self.n_cards_per_player - n_b + 1)
            ):
                actions_available.append((n_b, n_d))
        list_actions_available = [actions_available for _ in range(self.n_players)]

        # Return
        return rewards, self, self.list_is_playing_agents, list_obs, list_actions_available, False, {}

    def step(self, list_actions: List[Action]) -> Tuple[
        List[float],
        State,
        List[bool],
        List[Observation],
        List[ActionsAvailable],
        bool,
        Dict,
    ]:
        # Annoucement phase
        if self.game_phase == PhaseTimesBomb.ANNOUNCEMENT:
            # Annouce the number of bombs and diffuse wires
            self.common_obs.reset_global()
            for idx_player, action in enumerate(list_actions):
                n_b, n_d = action
                self.announcement[idx_player] = (n_b, n_d)
                self.common_obs.add_global_message(
                    f"Player {idx_player} announced : {n_b} bombs and {n_d} diffuse wires.",
                )
            # Call the next phase
            return self.start_new_cut()

        # Cut phase
        elif self.game_phase == PhaseTimesBomb.CUT:
            # Cut a wire
            self.common_obs.reset(self.player_cutter)
            idx_player_cut = list_actions[self.player_cutter]
            card_cut = self.hands[idx_player_cut].pop()
            self.previous_player_cutter = self.player_cutter
            self.cards_revealed.append(card_cut)
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
                        f"Player {self.player_cutter} cut the wire of player {idx_player_cut} and found a defusing wire. ({self.n_found_defuse}/{self.n_required_diffuse}). All defusing wires have been found. Agents win!"
                    )
                    return self.get_final_return(roles_win=[RoleTimesBomb.AGENT])
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
                        "2-card-per-player round is over but Agents have not found all defusing wires. Gangsters win."
                    )
                    return self.get_final_return(roles_win=[RoleTimesBomb.GANGSTER])
                elif self.n_cards_per_player == 0:
                    raise ValueError("All cards have been revealed without the game stopping.")
                
                # Start a new round
                return self.start_new_round()

            else:
                # Continue the cut phase
                return self.start_new_cut()
            
        else:
            raise ValueError(f"Unknown game phase : {self.game_phase}")

    def get_final_return(self, roles_win: List[RoleTimesBomb]) -> Tuple[
        List[float],
        State,
        List[bool],
        List[Observation],
        List[ActionsAvailable],
        bool,
        Dict,
    ]:
        rewards = [1 if role in roles_win else -1 for role in self.roles]
        self.common_obs.add_global_message("The game is over.")
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


class TimesBomb(BaseGame):

    def __init__(
        self,
        n_players: int,
        **kwargs,
    ) -> None:
        self.n_players = n_players
        self.config = kwargs

    def reset(
        self,
    ) -> Tuple[State, List[bool], List[Observation], List[ActionsAvailable], Dict]:
        state = StateTimesBomb(n_players=self.n_players, game=self, **self.config)
        return state.reset()

    def step(self, state: State, list_actions: List[Action]) -> Tuple[
        List[float],
        State,
        List[bool],
        List[Observation],
        List[ActionsAvailable],
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
                    if state.list_is_playing_agents[i]:
                        print(f"\n>>> Player {i} is playing :")
                        print(f"{state.common_obs[i]}")
                        if self.config["pause_at_each_step"]:
                            input()

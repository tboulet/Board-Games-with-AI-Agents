from boardgames.games.base_game import BaseGame
from boardgames.types import Action, ActionsAvailable, AgentID, Observation, State
from typing import Any, List, Optional, Tuple, Union, Dict

import random


CARD_LIBERAL = "Liberal Card"
CARD_FASCIST = "Fascist Card"

ROLE_LIBERAL = "Lib"
ROLE_FASCIST = "Fas"
ROLE_HITLER = "Hitler"

POWER_POLICY_PEEK = "Policy Peek"
POWER_INVESTIGATE = "Investigate"
POWER_SPECIAL_ELECTION = "Special Election"
POWER_BULLET_SHOT = "Bullet Shot"
POWER_FASCIST_WIN = "Fascist Win"


class CommonObservationsSH(list):
    def __init__(self, text: Optional[str] = "", n_players: int = 5) -> None:
        self.n_players = n_players
        super().__init__([text for _ in range(n_players)])

    def add_message(self, text: str, idx_player: int):
        if self[idx_player] in ["", None]:
            self[idx_player] = text
        else:
            self[idx_player] += f"\n{text}"

    def add_global_message(self, text: str, except_idx: Optional[int] = None):
        for i in range(self.n_players):
            if i != except_idx:
                self.add_message(text, i)

    def reset(self, idx_player: int):
        self[idx_player] = ""

    def reset_global(self):
        for i in range(self.n_players):
            self.reset(i)

    def __repr__(self) -> str:
        list_obs = [f"Player {i}: \n{self[i]}" for i in range(self.n_players)]
        return "Common Obs :\n" + "\n\n".join(list_obs)


class StateSH(State):
    def __init__(
        self,
        n_players: int,
        n_cards_liberal: int = 6,
        n_cards_fascist: int = 11,
        n_required_lib_policies: int = 5,
        n_required_fas_policies: int = 6,
        **kwargs,
    ) -> None:
        self.n_players = n_players
        self.n_cards_liberal = n_cards_liberal
        self.n_cards_fascist = n_cards_fascist
        self.n_required_lib_policies = n_required_lib_policies
        self.n_required_fas_policies = n_required_fas_policies
        self.common_obs = CommonObservationsSH(
            f"The game begins.\nDeck is shuffled ({n_cards_liberal} liberals and {n_cards_fascist} fascists).",
        )
        if n_players == 5:
            # Initialize roles
            self.roles = [ROLE_LIBERAL for _ in range(3)] + [ROLE_FASCIST, ROLE_HITLER]
            random.shuffle(self.roles)
            self.id_hitler = self.roles.index(ROLE_HITLER)
            self.ids_fascists = [
                i for i, role in enumerate(self.roles) if role == ROLE_FASCIST
            ]
            self.ids_liberals = [
                i for i, role in enumerate(self.roles) if role == ROLE_LIBERAL
            ]
            # Initialize policy deck
            self.policy_deck = [CARD_LIBERAL for _ in range(n_cards_liberal)] + [
                CARD_FASCIST for _ in range(n_cards_fascist)
            ]
            random.shuffle(self.policy_deck)
            self.policy_discard: List[str] = []
            # Get fascist board
            self.board_fas = [
                None,
                None,
                POWER_POLICY_PEEK,
                POWER_BULLET_SHOT,
                POWER_BULLET_SHOT,
                None,
            ]
            # Initialize game variables
            self.is_one_board_full: bool = False
            self.idx_player_playing: int = 0
            self.n_enabled_fas_policies: int = 0
            self.n_enabled_lib_policies: int = 0
            self.last_president: AgentID = None
            self.last_chancellor: AgentID = None
            self.candidate_president: AgentID = None
            self.candidate_chancellor: AgentID = None
            self.candidate_president_without_special_election: AgentID = None
            self.tracker: int = 0
            self.game_phase: str = "Nomination"
            self.is_alive: List[bool] = [True for _ in range(n_players)]
            self.idx_player_voting: int = None
            self.n_votes_yes: int = None
            self.n_votes_no: int = None
            self.votes: List[str] = [None for _ in range(n_players)]
            self.is_hitler_zone: bool = False
            self.is_veto_zone: bool = False
            self.card_vetoed: str = None
            self.veto_choice_chancellor: str = None
            self.veto_choice_president: str = None
            self.done: bool = False
            # Initialize player observations, as text
            for i in range(5):
                if self.roles[i] == ROLE_HITLER:
                    self.common_obs.add_message(
                        f"You are at seet {i}. \nYou get assigned the role Hitler. \nYou see the fascist with you is player {self.ids_fascists[0]}.",
                        i,
                    )
                elif self.roles[i] == ROLE_FASCIST:
                    self.common_obs.add_message(
                        f"You are at seet {i}. \nYou get assigned the role Fascist. \nYou see Hitler is player {self.id_hitler}.",
                        i,
                    )
                elif self.roles[i] == ROLE_LIBERAL:
                    self.common_obs.add_message(
                        f"You are at seet {i}. \nYou get assigned the role Liberal.", i
                    )
                else:
                    raise NotImplementedError("Role not implemented")
            self.start_next_nomination_phase()
        else:
            raise NotImplementedError("Only 5 players supported for now")

    def get_candidate_president_message(self) -> str:
        return f"You are the candidate president. You must propose a candidate chancellor among {self.get_possible_chancellor_candidates()}."

    def get_possible_chancellor_candidates(self) -> List[int]:
        return [
            i
            for i in range(self.n_players)
            if (not i in [self.last_chancellor, self.candidate_president])
            and self.is_alive[i]
        ]  # Only in 5 players or less

    def get_first_alive_player(self) -> int:
        idx_player = 0
        while not self.is_alive[idx_player]:
            idx_player += 1
        return idx_player

    def get_next_alive_player(self, idx_player: int) -> int:
        idx_player = (idx_player + 1) % self.n_players
        while not self.is_alive[idx_player]:
            idx_player = (idx_player + 1) % self.n_players
        return idx_player

    def get_next_candidate_president(self) -> int:
        if self.candidate_president is None:
            # If no candidate president, return the first alive player
            return self.get_first_alive_player()
        elif self.candidate_president_without_special_election is None:
            # If no special election, return the next player after the last candidate president
            return self.get_next_alive_player(self.candidate_president)
        else:
            # If special election, return the player that should have been candidate president if no special election
            temp = self.candidate_president_without_special_election
            self.candidate_president_without_special_election = None
            return temp

    def apply_policy(self, policy_enacted: str) -> None:
        if policy_enacted == CARD_LIBERAL:
            # If a lib policy is enacted, check if liberals win
            self.n_enabled_lib_policies += 1
            self.common_obs.add_global_message(
                f"A liberal policy is enacted. ({self.n_enabled_lib_policies}/{self.n_required_lib_policies})"
            )
            if self.n_enabled_lib_policies == self.n_required_lib_policies:
                self.common_obs.add_global_message("Liberals win !")
                self.is_one_board_full = True
                return

        elif policy_enacted == CARD_FASCIST:
            self.n_enabled_fas_policies += 1
            self.common_obs.add_global_message(
                f"A fascist policy is enacted. ({self.n_enabled_fas_policies}/{self.n_required_fas_policies})"
            )
            if self.n_enabled_fas_policies == self.n_required_fas_policies:
                self.common_obs.add_global_message("Fascists win ...")
                self.is_one_board_full = True
                return
            # Check if entering Hitler Zone
            if self.n_enabled_fas_policies == 3:
                self.common_obs.add_global_message(
                    "3 Fascist policies have been enacted, entering Hitler Zone : electing Hitler as Chancellor will win the game for the Fascists."
                )
                self.is_hitler_zone = True
            # Check if entering Veto Zone
            if self.n_enabled_fas_policies == 5:
                self.common_obs.add_global_message(
                    "5 Fascist policies have been enacted, entering Veto Zone : the Chancellor and President can veto a draw of policies if they both agree."
                )
                self.is_veto_zone = True
        else:
            raise NotImplementedError("Policy not implemented")

    def start_next_nomination_phase(self):
        # Get next candidate president
        self.candidate_president = self.get_next_candidate_president()
        # Create the observation of the next nomination
        self.common_obs.add_message(
            self.get_candidate_president_message(), self.candidate_president
        )
        # Entering nomination phase
        self.game_phase = "Nomination"
        self.actions_available = self.get_possible_chancellor_candidates()
        self.idx_player_playing = self.candidate_president

    def refill_deck_if_needed(self):
        if len(self.policy_deck) < 3:
            self.policy_deck += self.policy_discard
            assert (
                len(self.policy_deck) >= 3
            ), "Not enough cards in the (refilled) deck to draw 3 cards."
            self.policy_discard = []
            random.shuffle(self.policy_deck)
            self.common_obs.add_global_message(
                f"Deck is almost empty. Discard pile is shuffled back into the deck ({self.n_cards_liberal-self.n_enabled_lib_policies} liberals and {self.n_cards_fascist-self.n_enabled_fas_policies} fascists)."
            )

    def get_actions_available(self) -> List[Action]:
        list_actions = [[None] for _ in range(self.n_players)]
        list_actions[self.idx_player_playing] = self.actions_available
        return list_actions


class SecretHitlerGame(BaseGame):

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
        state = StateSH(self.n_players, **self.config)
        list_are_playing = self.empty_list_except(
            idx=state.idx_player_playing, value=True, fill=False
        )
        list_obs = self.empty_list_except(
            idx=state.idx_player_playing,
            value=state.common_obs[state.idx_player_playing],
        )
        list_actions_available = self.empty_list_except(
            idx=state.idx_player_playing, value=state.actions_available
        )
        return state, list_are_playing, list_obs, list_actions_available, {}

    def step(self, state: StateSH, list_actions: List[Action]) -> Tuple[
        List[float],
        StateSH,
        List[bool],
        List[Observation],
        List[ActionsAvailable],
        bool,
        Dict,
    ]:
        action = list_actions[state.idx_player_playing]
        # Nomination phase
        if state.game_phase == "Nomination":
            assert (
                action in state.get_possible_chancellor_candidates()
            ), f"Invalid action {action}"

            # Create the observation of the nomination announcement
            state.common_obs.reset(state.candidate_president)
            state.common_obs.add_global_message(
                f"Player {state.candidate_president} becomes the next president.",
                state.candidate_president,
            )
            state.common_obs.add_global_message(
                f"Player {state.candidate_president} nominated player {action} as chancellor.\nThe game proceeds to the voting phase. You must vote (Yes or No) for Government {state.candidate_president}-{action}."
            )

            # Entering voting phase, initialize the variables
            state.game_phase = "Voting"
            state.candidate_chancellor = action
            state.idx_player_voting = state.get_first_alive_player()
            state.n_votes_yes = 0
            state.n_votes_no = 0
            state.votes = [None for _ in range(state.n_players)]
            state.actions_available = ["Yes", "No"]
            state.idx_player_playing = state.idx_player_voting

        elif state.game_phase == "Voting":
            assert action in ["Yes", "No"], f"Invalid action {action}"

            # Process the vote
            state.votes[state.idx_player_voting] = action
            if action == "Yes":
                state.n_votes_yes += 1
            else:
                state.n_votes_no += 1

            # Create the observation of the vote
            state.common_obs.reset(state.idx_player_voting)
            state.common_obs.add_message(
                f"You voted {action}.", state.idx_player_voting
            )

            # Check if all players voted
            if state.n_votes_yes + state.n_votes_no == sum(state.is_alive):
                # If the vote passed, start the legislative phase
                if state.n_votes_yes > state.n_votes_no:
                    # Entering legislative (president) phase
                    state.game_phase = "Legislative (President)"
                    state.tracker = 0
                    state.last_president = state.candidate_president
                    state.last_chancellor = state.candidate_chancellor
                    # Create the observation of the vote result
                    state.common_obs.reset_global()
                    state.common_obs.add_global_message(
                        f"Votes are: {state.votes}. (Yes: {state.n_votes_yes}, No: {state.n_votes_no})\nGovernment passed."
                    )
                    # Check Hitler Chancellor election fascist victory criteria
                    if state.is_hitler_zone:
                        if state.last_chancellor == state.id_hitler:
                            state.common_obs.add_global_message(
                                f"Hitler was elected Chancellor. Fascists win ..."
                            )
                            return self.get_final_return(state)
                        else:
                            state.common_obs.add_global_message(
                                f"Player {state.last_chancellor} is confirmed not Hitler."
                            )
                    state.common_obs.add_global_message(
                        "The game proceeds to the legislative phase."
                    )

                    cards_drawn = (
                        state.policy_deck.pop(0),
                        state.policy_deck.pop(0),
                        state.policy_deck.pop(0),
                    )
                    state.common_obs.add_message(
                        f"You draw the following cards: {cards_drawn}. You must discard one.",
                        state.last_president,
                    )
                    state.actions_available = list(cards_drawn)
                    state.idx_player_playing = state.last_president

                # If the vote failed, move forward tracker
                else:
                    # Create the observation of the vote result
                    state.common_obs.add_global_message(
                        f"Votes are: {state.votes}. (Yes: {state.n_votes_yes}, No: {state.n_votes_no})\nVote failed and tracker move to {state.tracker+1}/3."
                    )
                    # Move forward the tracker and check if it reach Top Deck
                    state.tracker += 1
                    if state.tracker == 3:
                        state.common_obs.add_global_message(
                            "Tracker reached 3. The top policy is enacted."
                        )
                        state.tracker = 0
                        state.last_president = None
                        state.last_chancellor = None
                        policy_enacted = state.policy_deck.pop(0)
                        self.enact_policy(state, policy_enacted, on_top_deck=True)
                        # Check if the game is over
                        if state.is_one_board_full:
                            return self.get_final_return(state)
                    else:
                        # Entering nomination phase
                        state.start_next_nomination_phase()

            else:
                # Get the next player to vote
                state.idx_player_voting = state.get_next_alive_player(
                    state.idx_player_voting
                )
                state.idx_player_playing = state.idx_player_voting

        elif state.game_phase == "Legislative (President)":
            assert action in state.actions_available, f"Invalid action {action}"
            # Perform the policy discard
            state.actions_available.remove(action)
            state.policy_discard.append(action)
            # Manage the observations of president and chancellor
            state.common_obs.reset(state.last_president)
            state.common_obs.add_message(
                f"You discard the card {action} and pass the remaining 2 cards to the chancellor.",
                state.last_president,
            )
            state.common_obs.add_global_message(
                f"President pick the card to discards. The two remaining cards are passed to the chancellor.",
                except_idx=state.last_president,
            )
            state.common_obs.add_message(
                f"You receive the following cards: {state.actions_available}. You must pick one that will be enacted.",
                state.last_chancellor,
            )
            # Entering legislative (chancellor) phase
            state.game_phase = "Legislative (Chancellor)"
            state.idx_player_playing = state.last_chancellor

        elif state.game_phase == "Legislative (Chancellor)":
            assert action in state.actions_available, f"Invalid action {action}"
            # Create the observation of the policy enactment
            state.common_obs.reset(state.last_chancellor)
            state.common_obs.add_message(
                f"You pick the policy {action} and discards the other.",
                state.last_chancellor,
            )
            state.common_obs.add_global_message(
                f"The Chancellor pick the card to enact and discards the other.",
                except_idx=state.last_chancellor,
            )
            # In Veto Zone, Chancellor has the choice to veto
            if state.is_veto_zone:
                # Create the observation of the veto choice
                state.common_obs.add_global_message(
                    "The government can decide to veto the remaining policy. Both President and Chancellor must agree to veto."
                )
                state.common_obs.add_message(
                    f"You have the choice to veto the remaining policy. Do you want to veto ? (Yes or No)",
                    state.last_chancellor,
                )
                # Entering veto (chancellor) phase
                state.game_phase = "Veto (Chancellor)"
                state.actions_available = ["Yes", "No"]
                state.idx_player_playing = state.last_chancellor
                state.card_vetoed = action

            else:
                # Perform the policy enactment
                state.actions_available.remove(action)
                card_discarded = state.actions_available[0]
                state.policy_discard.append(card_discarded)
                self.enact_policy(state, action)
                # Check if the game is over
                if state.is_one_board_full:
                    return self.get_final_return(state)

        elif state.game_phase == "Investigation":
            assert (
                action in range(state.n_players)
                and state.is_alive[action]
                and action != state.last_president
            ), f"Invalid action {action}"
            # Create the observation of the investigation
            role_investigated = state.roles[action]
            if role_investigated == ROLE_LIBERAL:
                party_investigated = "Liberal"
            elif role_investigated in [ROLE_FASCIST, ROLE_HITLER]:
                party_investigated = "Fascist"
            state.common_obs.reset(state.last_president)
            state.common_obs.add_message(
                f"You investigate the party of player {action} and see that he is {party_investigated}.",
                state.last_president,
            )
            state.common_obs.add_global_message(
                f"President investigated the role of player {action}."
            )
            # Entering nomination phase
            state.start_next_nomination_phase()

        elif state.game_phase == "Special Election":
            assert action in state.actions_available, f"Invalid action {action}"
            # Create the observation of the special election
            state.common_obs.reset(state.last_president)
            state.common_obs.add_message(
                f"You choose player {action} as the next candidate president.",
                state.last_president,
            )
            state.common_obs.add_global_message(
                f"President choose player {action} as the next candidate president."
            )
            # Perform the special election effect
            state.candidate_president = action
            state.candidate_president_without_special_election = (
                state.get_next_alive_player(state.last_president)
            )
            # Entering nomination phase
            state.start_next_nomination_phase()

        elif state.game_phase == "Bullet Shot":
            assert action in state.actions_available, f"Invalid action {action}"
            # Kill the player
            role_killed = state.roles[action]
            state.common_obs.reset(state.last_president)
            state.common_obs.add_global_message(
                f"President {state.last_president} choose to kill player {action}.",
                except_idx=state.last_president,
            )
            state.common_obs.add_message(
                f"You have been killed by the President.", action
            )
            state.common_obs.add_message(
                f"You decided to kill player {action}.", state.last_president
            )
            state.is_alive[action] = False
            # Check Hitler death liberal victory criteria
            if role_killed == ROLE_HITLER:
                state.common_obs.add_global_message("Hitler is killed, liberals win !")
                return self.get_final_return(state)
            # Entering nomination phase
            state.start_next_nomination_phase()

        elif state.game_phase == "Veto (Chancellor)":
            assert action in ["Yes", "No"], f"Invalid action {action}"
            # Create the observation of the veto choice
            state.common_obs.reset(state.last_chancellor)
            state.common_obs.add_message(
                f"You voted {action} to veto the policy.",
                state.last_chancellor,
            )
            state.common_obs.add_message(
                f"You have the choice to veto the remaining policy. Do you want to veto ? (Yes or No)",
                state.last_president,
            )
            # Perform the veto choice
            state.veto_choice_chancellor = action
            # Entering veto (president) phase
            state.game_phase = "Veto (President)"
            state.idx_player_playing = state.last_president
            state.actions_available = ["Yes", "No"]

        elif state.game_phase == "Veto (President)":
            assert action in ["Yes", "No"], f"Invalid action {action}"
            # Create the observation of the veto choice
            state.common_obs.reset(state.last_president)
            state.common_obs.add_message(
                f"You voted {action} to veto the policy.",
                state.last_president,
            )
            # Perform the veto choice
            state.veto_choice_president = action
            is_card_vetoed = (state.veto_choice_chancellor == "Yes") and (
                state.veto_choice_president == "Yes"
            )
            if is_card_vetoed:
                state.common_obs.add_global_message(
                    "The policy is vetoed and discarded."
                )
                state.policy_discard.append(state.card_vetoed)
                # Check if refilling deck is needed
                state.refill_deck_if_needed()
                # Entering nomination phase
                state.start_next_nomination_phase()
            else:
                state.common_obs.add_global_message(
                    f"The veto is not applied (President: {state.veto_choice_president}, Chancellor: {state.veto_choice_chancellor})."
                )
                self.enact_policy(state, state.card_vetoed)
                state.card_vetoed = None
                # Check if the game is over
                if state.is_one_board_full:
                    return self.get_final_return(state)

        else:
            raise NotImplementedError("Game phase not implemented")

        # Return the next transition
        rewards = [0 for _ in range(self.n_players)]
        list_is_playing_agents = self.empty_list_except(
            idx=state.idx_player_playing, value=True, fill=False
        )
        list_obs = self.empty_list_except(
            idx=state.idx_player_playing,
            value=state.common_obs[state.idx_player_playing],
        )
        list_actions_available = self.empty_list_except(
            idx=state.idx_player_playing, value=state.actions_available
        )
        return (
            rewards,
            state,
            list_is_playing_agents,
            list_obs,
            list_actions_available,
            False,
            {},
        )

    def empty_list_except(self, idx: int, value: Any, fill: Any = None) -> List[Any]:
        """Create a list of size n_players with all elements set to fill except the one at idx set to value.

        Args:
            idx (int): the index of the value to set
            value (Any): the value to set at index idx
            fill (Any, optional): the fill value. Defaults to None.

        Returns:
            List[Any]: the list of n_players elements
        """
        list = [fill for _ in range(self.n_players)]
        list[idx] = value
        return list

    def get_n_players(self) -> int:
        return self.n_players

    def get_list_actions_available(self, state: StateSH) -> List[List[Action]]:
        return state.get_actions_available()

    def render(self, state: StateSH) -> None:
        if self.config["print_common_obs"]:
            print(state.common_obs)

        if self.config["print_obs"]:
            if state.done:
                print(f"The game is over. : {state.common_obs}")
            else:
                i = state.idx_player_playing
                print(f"\n>>> Player {i} is playing :")
                print(f"{state.common_obs[i]}")

        if self.config["pause_at_each_step"]:
            input()

    def enact_policy(self, state: StateSH, action: str, on_top_deck=False) -> None:
        state.apply_policy(action)
        # Check if the game is over
        if state.is_one_board_full:
            return
        # Check if refilling deck is needed
        state.refill_deck_if_needed()
        # In case of a fascist policy, check if a power is activated
        if action == CARD_FASCIST:
            power_activated = state.board_fas[state.n_enabled_fas_policies - 1]
            if on_top_deck:
                power_activated = None  # nullify power if on top deck
            if power_activated == POWER_POLICY_PEEK:
                # Create the observation of the policy peek
                state.common_obs.add_global_message(
                    "'Policy Peek' power is activated. President investigate the top 3 cards of the deck."
                )
                state.common_obs.add_message(
                    f"You investigate the 3 next cards: {state.policy_deck[:3]}.",
                    state.last_president,
                )
                # Entering nomination phase
                state.start_next_nomination_phase()
            elif power_activated == POWER_INVESTIGATE:
                # Create the observation of the investigation
                state.common_obs.add_global_message(
                    "'Investigation' power is activated. President must investigate the role of an other player."
                )
                possible_player_to_investigate = [
                    i
                    for i in range(self.n_players)
                    if i != state.last_president and state.is_alive[i]
                ]
                state.common_obs.add_message(
                    f"You must investigate the role of an other living player (among {possible_player_to_investigate}).",
                    state.last_president,
                )
                # Entering investigation phase
                state.game_phase = "Investigation"
                state.actions_available = possible_player_to_investigate
                state.idx_player_playing = state.last_president
            elif power_activated == POWER_SPECIAL_ELECTION:
                # Create the observation of the special election
                state.common_obs.add_global_message(
                    "'Special Election' power is activated. President must choose the next candidate president."
                )
                possible_next_presidents = [
                    i
                    for i in range(self.n_players)
                    if i != state.last_president and state.is_alive[i]
                ]
                state.common_obs.add_message(
                    f"You must choose the next candidate president (among {possible_next_presidents}).",
                    state.last_president,
                )
                # Entering special election
                state.game_phase = "Special Election"
                state.actions_available = possible_next_presidents
                state.idx_player_playing = state.last_president
            elif power_activated == POWER_BULLET_SHOT:
                # Create the observation of the bullet shot
                state.common_obs.add_global_message(
                    "'Bullet Shot' power is activated. President must choose a player to kill."
                )
                possible_players_to_kill = [
                    i
                    for i in range(self.n_players)
                    if i != state.last_president and state.is_alive[i]
                ]
                state.common_obs.add_message(
                    f"You must choose a player to kill (among {possible_players_to_kill}).",
                    state.last_president,
                )
                # Entering bullet shot
                state.game_phase = "Bullet Shot"
                state.actions_available = possible_players_to_kill
                state.idx_player_playing = state.last_president
            elif power_activated == None:
                # Entering nomination phase
                state.start_next_nomination_phase()
            else:
                raise NotImplementedError("Power not implemented")
        else:
            # Entering nomination phase
            state.start_next_nomination_phase()

    def get_final_return(self, state: StateSH) -> Tuple[
        List[float],
        StateSH,
        List[bool],
        List[Observation],
        List[ActionsAvailable],
        bool,
        Dict,
    ]:
        if (
            state.n_enabled_lib_policies == state.n_required_lib_policies
            or not state.is_alive[state.id_hitler]
        ):
            rewards = [
                1 if role == ROLE_LIBERAL else -1 for role in state.roles
            ]  # rewards if lib win
        elif state.n_enabled_fas_policies == state.n_required_fas_policies or (
            state.is_hitler_zone and state.last_chancellor == state.id_hitler
        ):
            rewards = [-1 if role == ROLE_LIBERAL else 1 for role in state.roles]
        else:
            raise NotImplementedError("Game not over but final return called")
        state.common_obs.add_global_message("The game is over.")
        state.done = True
        return (
            rewards,
            state,
            [False for _ in range(state.n_players)],
            state.common_obs,
            [None for _ in range(state.n_players)],
            True,
            {},
        )

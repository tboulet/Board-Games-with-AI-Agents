from collections import defaultdict
import random
from typing import List, Tuple
from boardgames.games.werewolves.factions import FactionsWW
from boardgames.games.werewolves.phase.base_phase import Phase
from boardgames.games.werewolves.roles.base_role import RoleWW
from boardgames.games.werewolves.state import CauseWolfAttack, StateWW, StatusIsWolf
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


class PhaseNightWolfSpeech(Phase):

    def get_name(self) -> str:
        return "Night Wolf Speech"

    def play_action(self, state: StateWW, joint_action: JointAction) -> StateWW:

        # Treat the speech
        id_wolf_speaking = state.order_speech_wolf[state.idx_speech_wolf]
        assert (
            joint_action[id_wolf_speaking] is not None
        ), f"Player {id_wolf_speaking} must speak."
        list_id_wolves = state.get_list_id_wolves_alive()
        state.common_obs.add_specific_message(
            text=f"[Private Wolf Chat] Player {id_wolf_speaking} says : {joint_action[id_wolf_speaking]}",
            list_idx_player=list_id_wolves,
            except_idx=id_wolf_speaking,
        )
        state.common_obs.add_message(
            text=f"[Private Wolf Chat] You say : {joint_action[id_wolf_speaking]}",
            idx_player=id_wolf_speaking,
        )

        # # Send partial message to the little girl
        # if RoleLittleGirl() in [
        #     state.identities[i].role
        #     for i in range(self.n_players)
        #     if state.list_are_alive[i]
        # ]:
        #     message_little_girl = RoleLittleGirl().partially_hide_message(
        #         message=joint_action[id_wolf_speaking],
        #         config_little_girl=self.config["config_little_girl"],
        #     )
        #     id_little_girl = self.get_id_player_with_role(state, RoleLittleGirl())
        #     state.common_obs.add_message(
        #         text=f"[Little Girl spying] {message_little_girl}",
        #         idx_player=id_little_girl,
        #     )

        # Move to the next speaker
        state.idx_speech_wolf += 1

        # Check if all wolves have spoken
        if state.idx_speech_wolf >= len(state.order_speech_wolf):
            # Announcing the end of the night wolf speech
            state.common_obs.add_specific_message(
                "All wolves have spoken, now is the time to choose your target.",
                list_idx_player=list_id_wolves,
            )
            # Move to the next phase
            state.phase_manager.advance_phase()
            # Reset the speech variables for good measure
            state.order_speech_wolf = None
            state.idx_speech_wolf = None

    def return_feedback(self, state: StateWW) -> Tuple[
        JointReward,
        JointPlayingInformation,
        JointObservation,
        JointActionSpace,
        TerminalSignal,
        InfoDict,
    ]:
        if state.order_speech_wolf is None:
            # Announce the beginning of the night wolf speech and set up the night wolf speech variables
            state.start_new_night_wolf_speech()
        if len(state.order_speech_wolf) == 0:
            breakpoint()
        id_wolf_speaking = state.order_speech_wolf[state.idx_speech_wolf]
        list_id_wolves_alive = state.get_list_id_wolves_alive()
        state.common_obs.add_specific_message(
            f"[Private Wolf Chat] Player {id_wolf_speaking} is now speaking.",
            list_idx_player=list_id_wolves_alive,
            except_idx=id_wolf_speaking,
        )
        state.common_obs.add_message(
            text="[Private Wolf Chat] You are now speaking. Please express yourself about the current situation with the other wolves.",
            idx_player=id_wolf_speaking,
        )
        return state.get_return_feedback_one_player(
            id_player=id_wolf_speaking,
            action_space=TextualActionSpace(
                description="Express yourself about the current situation."
            ),
        )

    def is_day_phase(self) -> bool:
        return False


class PhaseNightWolfVote(Phase):

    def get_name(self) -> str:
        return "Night Wolf Vote"

    def play_action(self, state: StateWW, joint_action: JointAction) -> StateWW:

        report_attack = ""
        attack_count = defaultdict(int)
        list_id_wolves_alive = state.get_list_id_wolves_alive()
        # Count the votes
        for id_player, id_target in enumerate(joint_action):
            if id_target is not None:
                assert (
                    id_player in list_id_wolves_alive
                ), f"Player {id_player} is not an alive wolf but has chosen to attack player {id_target}."
                report_attack += f"Wolf {id_player} voted for player {id_target}.\n"
                attack_count[id_target] += 1
        state.common_obs.add_specific_message(
            text=f"[Private Wolf Chat] The wolves have voted for their target : \n{report_attack}",
            list_idx_player=list_id_wolves_alive,
        )
        most_attacked_players = [
            id_player
            for id_player, count in attack_count.items()
            if count == max(attack_count.values())
        ]
        # If there is a draw, pick a player randomly among the tied players
        if len(most_attacked_players) > 1:
            id_target_final: int = random.choice(most_attacked_players)
            state.common_obs.add_specific_message(
                f"[Private Wolf Chat] There is a draw in the votes of the wolves. Eliminated player is picked randomly among the tied players : {id_target_final}.",
                list_idx_player=list_id_wolves_alive,
            )
        else:
            id_target_final: int = most_attacked_players[0]
        state.common_obs.add_specific_message(
            f"[Private Wolf Chat] The wolves have chosen their target : player {id_target_final}.",
            list_idx_player=list_id_wolves_alive,
        )
        state.common_obs.log(
            f"The wolves have chosen their target : player {id_target_final}.",
            "ACTION",
        )
        # Check if the target is protected
        attack_fails = False
        # if state.identities[id_target_final].have_status(
        #     Status.IS_PROTECTED_SAVIOR
        # ):
        #     if RoleBodyguard() in [
        #         state.identities[i].role
        #         for i in range(self.n_players)
        #         if state.list_are_alive[i]
        #     ]:  # only works if the bodyguard is alive this night
        #         attack_fails = True
        # if state.identities[id_target_final].have_status(Status.IS_PROTECTED_ELDER):
        #     state.identities[id_target_final].remove_status(
        #         Status.IS_PROTECTED_ELDER
        #     )
        #     attack_fails = True
        # if state.identities[id_target_final].have_status(
        #     Status.IS_PROTECTED_RED_HOOD
        # ):
        #     attack_fails = True
        # # Add the target to the list of deaths
        if not attack_fails:
            state.night_attacks[id_target_final].add(CauseWolfAttack())
        # Advance to the next phase
        state.phase_manager.advance_phase()
        return state

    def return_feedback(self, state: StateWW) -> Tuple[
        JointReward,
        JointPlayingInformation,
        JointObservation,
        JointActionSpace,
        TerminalSignal,
        InfoDict,
    ]:
        list_id_villagers_alive_as_str = [
            str(i) for i in range(state.n_players) if state.list_are_alive[i]
        ]
        list_id_wolves_alive = state.get_list_id_wolves_alive()
        state.common_obs.add_specific_message(
            f"[Private Wolf Chat] The wolves must now choose their target. Pick a player to eliminate among the villagers : {list_id_villagers_alive_as_str}.",
            list_idx_player=list_id_wolves_alive,
        )
        rewards = [0.0] * state.n_players
        list_is_playing = [i in list_id_wolves_alive for i in range(state.n_players)]
        list_obs = (
            state.common_obs
        )  # this include non playing player but should not be a problem
        list_action_spaces = [
            FiniteActionSpace(actions=list_id_villagers_alive_as_str)
        ] * state.n_players  # same
        return (
            rewards,
            list_is_playing,
            list_obs,
            list_action_spaces,
            False,
            {},
        )

    def is_day_phase(self) -> bool:
        return False


class RoleWerewolf(RoleWW):
    @classmethod
    def get_name(cls) -> str:
        return "Wolf"

    @classmethod
    def get_initial_faction(cls) -> FactionsWW:
        return FactionsWW.WEREWOLVES

    def get_initial_statutes(self) -> List[Status]:
        return [StatusIsWolf()]

    def get_associated_phases(self) -> List[str]:
        return [PhaseNightWolfSpeech(), PhaseNightWolfVote()]

    @classmethod
    def get_textual_description(cls) -> str:
        return (
            "Role: Werewolf. Your objective is to eliminate all Villagers and special roles without being discovered. "
            "Each night, you secretly collaborate with the other Werewolves to choose a player to eliminate. "
            "During the day, you must blend in, act innocent, and influence discussions to protect yourself and your allies. "
            "Key Abilities: "
            "- Night Kill: Each night, coordinate with fellow Werewolves to select a player to eliminate. "
            "- Deception: During the day, you must lie, manipulate, and cast suspicion on others to avoid being identified. "
            "- Team Strategy: Work closely with other Werewolves but avoid making your alliances too obvious. "
            "Winning Condition: You win when all Villagers and special roles are eliminated, or when the Werewolves equal or outnumber the remaining players. "
            "Strategic Tips: "
            "- Accuse others subtly to avoid suspicion. "
            "- Deflect attention by carefully supporting or opposing popular opinions. "
            "- Decide when to defend or distance yourself from fellow Werewolves under suspicion to survive longer. "
            "Blend in, deceive the Villagers, and eliminate them one by one to secure victory."
        )

    @classmethod
    def get_short_textual_description(cls) -> str:
        return "The base role of the werewolves. Wakes up at night with the other werewolves to choose a player to eliminate"

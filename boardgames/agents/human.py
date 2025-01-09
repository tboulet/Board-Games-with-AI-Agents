from typing import Any, Dict, List

import numpy as np
from boardgames.agents.base_agents import BaseAgent
from boardgames.types import Observation, Action, State, AgentID
from boardgames.action_spaces import ActionsSpace, TextualActionSpace
import random


class HumanAgent(BaseAgent):

    def __init__(self, print_info: bool = False):
        self.print_info = print_info

    def act(self, observation: Observation, action_space: ActionsSpace) -> Action:
        print()
        print(observation)
        action = input("Enter your move: ")
        action = self.read_action(action, action_space)
        while action not in action_space:
            print(
                f"Invalid move : {action, type(action)} Please follow the restrictions: {action_space.get_textual_restrictions()}"
            )
            action = input("Enter your move: ")
            action = self.read_action(action, action_space)
        print(f"You chose action : {action}")
        return action

    def learn(
        self,
        is_playing: bool,
        action_space: ActionsSpace,
        observation: Observation,
        action: Action,
        reward: float,
        next_is_playing: bool,
        next_observation: Observation,
        next_action_space: ActionsSpace,
        done: bool,
    ):
        if self.print_info:
            print(f"\n INFORMATIONS")
            print(f"Is playing: {is_playing}")
            print(f"Action space: {action_space}")
            print(f"Observation: {observation}")
            print(f"Action: {action}")
            print(f"Reward: {reward}")
            print(f"Next is playing: {next_is_playing}")
            print(f"Next action space: {next_action_space}")
            print(f"Next observation: {next_observation}")
            print(f"Done: {done}")
            print()
        if done:
            print()
            print(next_observation)

    def read_action(self, action: Any, action_space : ActionsSpace) -> Action:
        return str(action)

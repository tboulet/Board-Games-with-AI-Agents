from typing import Dict, List

import numpy as np
from boardgames.agents.base_agents import BaseAgent
from boardgames.types import ActionsAvailable, Observation, Action, State, AgentID

import random


class HumanAgent(BaseAgent):

    def __init__(self, print_info: bool = False):
        self.print_info = print_info

    def act(self, observation: Observation, actions_available: List) -> Action:
        print()
        print(observation)
        action = input("Enter your move: ")
        if action.isdigit():
            action = int(action)
        while action not in actions_available:
            print("Invalid move. Please try again.")
            action = input("Enter your move: ")
            if action.isdigit():
                action = int(action)
        print(f"You chose {action}")
        return action
            
    def learn(
        self,
        is_playing: bool,
        actions_available: ActionsAvailable,
        observation: Observation,
        action: Action,
        reward: float,
        next_is_playing: bool,
        next_observation: Observation,
        next_actions_available: ActionsAvailable,
        done: bool,
    ):
        if self.print_info:
            print(f"\n INFORMATIONS")
            print(f"Is playing: {is_playing}")
            print(f"Actions available: {actions_available}")
            print(f"Observation: {observation}")
            print(f"Action: {action}")
            print(f"Reward: {reward}")
            print(f"Next is playing: {next_is_playing}")
            print(f"Next actions available: {next_actions_available}")
            print(f"Next observation: {next_observation}")
            print(f"Done: {done}")
            print()
        if done:
            print()
            print(next_observation)

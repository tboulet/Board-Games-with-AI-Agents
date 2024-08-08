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
        action = self.read_str_action(action)    
        while action not in actions_available:
            print(f"Invalid move : {action, type(action)} Please choose one of {actions_available}")
            action = input("Enter your move: ")
            action = self.read_str_action(action)
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

    def read_str_action(self, action: str):
        # Turn "0" into 0
        if action.isdigit():
            action = int(action)
        # Turn "0 1" into (0, 1)
        elif " " in action and all([x.isdigit() for x in action.split()]):
            action = tuple([int(x) for x in action.split()])
        return action
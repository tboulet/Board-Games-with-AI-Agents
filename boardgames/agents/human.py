from typing import Dict, List

import numpy as np
from boardgames.agents.base_agents import BaseAgent
from boardgames.types import ActionsAvailable, Observation, Action, State, AgentID

import random


class HumanAgent(BaseAgent):

    def __init__(self):
        pass

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
        if done:
            print()
            print(next_observation)

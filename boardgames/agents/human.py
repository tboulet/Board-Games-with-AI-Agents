from typing import Dict, List

import numpy as np
from boardgames.agents.base_agents import BaseAgent
from boardgames.types import Observation, Action, State, AgentID

import random


class HumanAgent(BaseAgent):

    def __init__(self):
        pass

    def act(self, observation: Observation, actions_available: List) -> Action:
        print(observation)
        action = input("Enter your move: ")
        if action.isdigit():
            action = int(action)
        while action not in actions_available:
            print("Invalid move. Please try again.")
            action = input("Enter your move: ")
            if action.isdigit():
                action = int(action)
        return action
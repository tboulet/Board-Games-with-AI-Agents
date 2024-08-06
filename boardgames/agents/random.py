from typing import Dict, List

import numpy as np
from boardgames.agents.base_agents import BaseAgent
from boardgames.types import Observation, Action, State, AgentID

import random


class RandomAgent(BaseAgent):

    def __init__(self):
        pass

    def act(self, observation: Observation, actions_available: List) -> Action:
        return random.choice(actions_available)

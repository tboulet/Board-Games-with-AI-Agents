from typing import Dict, List

import numpy as np
from boardgames.agents.base_agents import BaseAgent
from boardgames.types import ActionsAvailable, Observation, Action, State, AgentID

import random


class RandomAgent(BaseAgent):

    def __init__(self):
        pass

    def act(self, observation: Observation, actions_available: List) -> Action:
        return random.choice(actions_available)
    
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
        pass

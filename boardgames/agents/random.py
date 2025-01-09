from typing import Dict, List

import numpy as np
from boardgames.agents.base_agents import BaseAgent
from boardgames.types import Observation, Action, State, AgentID
from boardgames.action_spaces import ActionsSpace, FiniteActionSpace, K_AmongFiniteActionSpace, TextualActionSpace
import random
import string

class RandomAgent(BaseAgent):

    def __init__(self):
        pass

    def act(self, observation: Observation, action_space: ActionsSpace) -> Action:
        if isinstance(action_space, FiniteActionSpace):
            return random.choice(action_space.actions)
        elif isinstance(action_space, TextualActionSpace):
            # Random string
            length = random.randint(4, 10)
            characters = string.ascii_letters + string.digits  # Uppercase, lowercase, and digits
            random_string = ''.join(random.choice(characters) for _ in range(length))
            return random_string 
        elif isinstance(action_space, K_AmongFiniteActionSpace):
            return random.sample(action_space.actions, action_space.k)
        else:
            raise NotImplementedError(f"Action space {action_space} not supported.")
        
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
        pass

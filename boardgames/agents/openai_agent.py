import os
import re
from typing import Dict, List, Union

import numpy as np
from boardgames.agents.base_agents import BaseAgent
from boardgames.agents.base_text_agents import BaseTextAgent
from boardgames.types import Observation, Action, State, AgentID
from boardgames.action_spaces import ActionsSpace

import random
from openai import OpenAI


class OpenAI_Agent(BaseTextAgent):
    is_active: bool = False
    client: OpenAI = None

    def __init__(self, model: str, do_print_reasoning: bool = True):
        self.try_connect()
        self.model = model
        self.do_print_reasoning = do_print_reasoning
        self.messages: List[Dict[str, str]] = []

    def act(self, observation: Observation, action_space: ActionsSpace) -> Action:
        # Add the observation (plus available actions) to the messages
        content = observation + f"\nAction restriction: {action_space.get_textual_restrictions()}"
        self.messages.append({"role": "user", "content": content})

        # Get the assistant's answer
        answer_assistant = (
            self.client.chat.completions.create(
                model=self.model,  # Replace with your preferred model
                messages=self.messages,
            )
            .choices[0]
            .message.content
        )

        # Add the assistant's answer to the messages
        self.messages.append(
            {"role": "assistant", "content": f"I play action {answer_assistant}"}
        )

        # Extract the action from the assistant's answer
        action = self.extract_action(answer_assistant, action_space)
        if action is not None:
            if self.do_print_reasoning:
                print(f"ASSISTANT ANSWER: {answer_assistant}")
            return action

        # Loop until the assistant provides a valid action
        for _ in range(10):
            print(f"Warning : the assistant provided an invalid action.")
            self.messages.append(
                {
                    "role": "system",
                    "content": f"You chose an invalid action: {action}. Please respect these restrictions: {action_space.get_textual_restrictions()} and answer in the following format: 'Reasonning : <your reasonning>\nAction:\n<your action>'",
                }
            )
            answer_assistant = (
                self.client.chat.completions.create(
                    model=self.model,
                    messages=self.messages,
                )
                .choices[0]
                .message.content
            )
            action = self.extract_action(answer_assistant, action_space)
            if action is not None:
                print("Solved : the corrected and provided a valid action.")
                if self.do_print_reasoning:
                    print(f"Reasonning of agent: {answer_assistant}")
                return action

        raise ValueError(f"Assistant provided an invalid action 10 times in a row : \n\n{answer_assistant=}, \n\n{action_space=}, \n\n{self.messages=}")
            
            
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

    def set_game_context(self, game_context: str):
        self.messages.append({"role": "system", "content": game_context})

    def try_connect(self):
        if not OpenAI_Agent.is_active:
            print("Connecting to OpenAI's API...")
            OpenAI_Agent.client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
            OpenAI_Agent.is_active = True
            print("Connected to OpenAI API !")

    def extract_action(
        self, answer_assistant: str, action_space: ActionsSpace
    ) -> Action:
        """Extract the action from the assistant's answer.

        Args:
            answer_assistant (str): the assistant's answer
            action_space (ActionsSpace): the action space
            
        Returns:
            Action: the action to play
        """
        action_match = re.search(r"Action:\s*(.+)", answer_assistant)
        if not action_match:
            print(f"Warning : no action found in the assistant's answer.")
            return None  # No action found : return None to signal the error
        action = action_match.group(1) # .strip() ?
        if not action in action_space:
            return None  # Action not in action space : return None to signal the error 
        return action

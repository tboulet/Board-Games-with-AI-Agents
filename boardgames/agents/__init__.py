from typing import Dict, Type
from boardgames.agents.base_agents import BaseAgent
from boardgames.agents.random import RandomAgent


agent_name_to_AgentClass: Dict[str, Type[BaseAgent]] = {
    "RandomAgent": RandomAgent,
}

# Logging
import os
import wandb
from tensorboardX import SummaryWriter

# Config system
import hydra
from omegaconf import OmegaConf, DictConfig

# Utils
from tqdm import tqdm
import datetime
from time import time, sleep
from typing import Dict, List, Type
import cProfile

# ML libraries
import random
import numpy as np

# Project imports
from boardgames.types import Observation, Action, State, AgentID, RewardVector
from boardgames.agents.base_agents import BaseAgent
from boardgames.time_measure import RuntimeMeter
from boardgames.utils import instantiate_class, try_get_seed
from boardgames.games import game_name_to_GameClass
from boardgames.agents import agent_name_to_AgentClass


@hydra.main(config_path="configs", config_name="config_default.yaml")
def main(config: DictConfig):
    print("Configuration used :")
    print(OmegaConf.to_yaml(config))
    config = OmegaConf.to_container(config, resolve=True)

    # Get the config values from the config object.
    agents_name: str = config["agents"]["name"]
    game_name: str = config["game"]["name"]
    n_iterations: int = config["n_iterations"]
    do_cli: bool = config["do_cli"]
    do_wandb: bool = config["do_wandb"]
    do_tb: bool = config["do_tb"]
    do_tqdm: bool = config["do_tqdm"]

    # Set the seeds
    seed = try_get_seed(config)
    random.seed(seed)
    np.random.seed(seed)
    print(f"Using seed: {seed}")

    # Create the game
    print("Creating the game...")
    GameClass = game_name_to_GameClass[game_name]
    game = GameClass(**config["game"]["config"])
    n_players = game.get_n_players()

    # Get the agents
    print("Creating the agents...")
    agents: List[BaseAgent] = [
        instantiate_class(**config["agents"]["configs_agents"][i]) for i in range(n_players)
    ]

    # Initialize loggers
    run_name = f"[{agents_name}]_[{game_name}]_{datetime.datetime.now().strftime('%dth%mmo_%Hh%Mmin%Ss')}_seed{np.random.randint(seed)}"
    os.makedirs("logs", exist_ok=True)
    print(f"\nStarting run {run_name}")
    if do_wandb:
        run = wandb.init(
            name=run_name,
            config=config,
            **config["wandb_config"],
        )
    if do_tb:
        tb_writer = SummaryWriter(log_dir=f"tensorboard/{run_name}")

    # Game loop
    print("\nStarting the game loop...")
    state, obs, agent_id, info = game.reset()
    done = False
    game.render(state)
    while not done:
        agent: BaseAgent = agents[agent_id]
        actions_available = game.get_actions_available(state)
        action = agent.act(obs, actions_available)
        next_state, next_obs, rewards, next_agent_id, done, info = game.step(
            state, action
        )
        # Logging
        game.render(next_state)
        if len(info) != 0:
            print(f"INFO: {info}")
        # Update the state of the loop
        state = next_state
        obs = next_obs
        agent_id = next_agent_id

    print("Game over!")
    print(f"Rewards: {rewards}")

    # Finish the WandB run.
    if do_wandb:
        run.finish()


if __name__ == "__main__":
    with cProfile.Profile() as pr:
        main()
    pr.dump_stats("logs/profile_stats.prof")
    print("\nProfile stats dumped to profile_stats.prof")
    print(
        "You can visualize the profile stats using snakeviz by running 'snakeviz logs/profile_stats.prof'"
    )

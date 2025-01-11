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
from boardgames.agents.base_text_agents import BaseTextAgent
from boardgames.games.base_text_game import BaseTextBasedGame
from boardgames.types import Observation, Action, State, AgentID, JointReward
from boardgames.agents.base_agents import BaseAgent
from boardgames.time_measure import RuntimeMeter
from boardgames.utils import instantiate_class, try_get_seed
from boardgames.hydra_utils import register_resolvers
from boardgames.games import game_name_to_GameClass

# Register the resolvers
register_resolvers()

@hydra.main(config_path="configs", config_name="config_default.yaml")
def main(config: DictConfig):
    print("Configuration used :")
    print(OmegaConf.to_yaml(config))
    config = OmegaConf.to_container(config, resolve=True)

    # Get the config values from the config object.
    agents_name: str = config["agents"]["name"]
    game_name: str = config["game"]["name"]
    do_cli: bool = config["do_cli"]
    do_wandb: bool = config["do_wandb"]
    do_tb: bool = config["do_tb"]
    do_tqdm: bool = config["do_tqdm"]

    # Set the seeds
    seed = try_get_seed(config)
    random.seed(seed)
    np.random.seed(seed)
    print(f"Using seed: {seed}")

    # Initialize loggers
    run_name = f"[{agents_name}]_[{game_name}]_{datetime.datetime.now().strftime('%dth%mmo_%Hh%Mmin%Ss')}_seed{seed}"
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
        
    # Create the game
    print("Creating the game...")
    GameClass = game_name_to_GameClass[game_name]
    game = GameClass(**config["game"]["config"], seed=seed, run_name=run_name)
    n_players = game.get_n_players()

    # Get the agents
    print("Creating the agents...")
    agents: List[BaseAgent] = [
        instantiate_class(**config["agents"]["configs_agents"][i])
        for i in range(n_players)
    ]
    agents_text_based: List[BaseTextAgent] = [
        agent for agent in agents if isinstance(agent, BaseTextAgent)
    ]
    if len(agents_text_based) > 0:
        assert isinstance(
            game, BaseTextBasedGame
        ), "The game must be text-based to use text-based agents."
        game_context = game.get_game_context()
        for agent in agents_text_based:
            agent.set_game_context(game_context)

    # Game loop
    print("\nStarting the game loop...")
    state, list_is_playing_agents, list_obs, list_action_spaces, info = game.reset()
    done = False
    game.render(state)
    while not done:
        list_actions = []
        # Play each agent
        for idx_agent in range(n_players):
            if list_is_playing_agents[idx_agent]:
                # Get the agent and corresponding observation and actions available
                agent: BaseAgent = agents[idx_agent]
                action_space = list_action_spaces[idx_agent]
                obs = list_obs[idx_agent]
                # Agent acts
                action = agent.act(observation=obs, action_space=action_space)
                assert (
                    action in action_space
                ), f"Invalid action : '{action}' for agent {idx_agent}. Action space: {action_space}"
                list_actions.append(action)
            else:
                list_actions.append(None)
        # Step the game
        (
            rewards,
            next_state,
            next_list_is_playing_agents,
            next_list_obs,
            next_list_action_spaces,
            done,
            info,
        ) = game.step(state, list_actions)
        # Learn each agent
        for idx_agent in range(n_players):
            agent = agents[idx_agent]
            obs = list_obs[idx_agent]
            action_space = list_action_spaces[idx_agent]
            is_playing = list_is_playing_agents[idx_agent]
            action = list_actions[idx_agent]
            reward = rewards[idx_agent]
            next_is_playing = next_list_is_playing_agents[idx_agent]
            next_observation = (
                next_list_obs[idx_agent] if (next_is_playing or done) else None
            )  # Possibly let this even if not next_is_playing for optimizing learning
            next_action_space = (
                next_list_action_spaces[idx_agent] if next_is_playing else None
            )  # Possibly let this even if not next_is_playing for optimizing learning
            agent.learn(
                is_playing=is_playing,
                observation=obs,
                action_space=action_space,
                action=action,
                reward=reward,
                next_is_playing=next_is_playing,
                next_observation=next_observation,
                next_action_space=next_action_space,
                done=done,
            )
        # Logging
        game.render(next_state)
        if len(info) != 0:
            print(f"INFO: {info}")
        # Update the state of the loop
        state = next_state
        list_obs = next_list_obs
        list_action_spaces = next_list_action_spaces
        list_is_playing_agents = next_list_is_playing_agents

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

import os
from typing import Dict, List, Optional, Tuple, Union
import logging


class CommonObs(list):
    def __init__(
        self,
        text: Optional[str] = "",
        n_players: int = 5,
        list_log_files: List[str] = None,
        config_log : Dict[str, Union[str, int]] = {},
    ) -> None:
        self.n_players = n_players
        # Initialize the logger if logging is enabled
        if list_log_files is not None:
            self.do_log_messages = config_log.get("do_log_messages", False)
            self.do_log_infos = config_log.get("do_log_infos", False)
            self.logger = logging.getLogger("Game Logger")
            self.logger.setLevel(logging.DEBUG)
            assert isinstance(
                list_log_files, list
            ), "log_files must be a list of strings or None if no logging is desired"
            assert isinstance(config_log, dict), "config_log must be a dictionary"
            for log_file in list_log_files:
                # Remove the file if it already exists and recreate it
                if os.path.exists(log_file):
                    os.remove(log_file)
                os.makedirs(os.path.dirname(log_file), exist_ok=True)
                file_handler = logging.FileHandler(log_file)
                file_handler.setLevel(logging.DEBUG)
                file_handler.setFormatter(
                    logging.Formatter(config_log.get("log_format", "%(asctime)s - %(message)s\n"))
                )
                self.logger.addHandler(file_handler)
        else:
            self.logger = None
            self.do_log_messages = False
            self.do_log_infos = False
        super().__init__([text for _ in range(n_players)])

    def add_message(self, text: str, idx_player: int, do_log: bool = True):
        """Add a message to the observation of a player."""
        if self[idx_player] in ["", None]:
            self[idx_player] = text
        else:
            self[idx_player] += f"\n{text}"
        # Log the message
        if self.do_log_messages and do_log:
            self.logger.info(f"[MESSAGE] Message to player {idx_player} : {text}")

    def add_specific_message(
        self,
        text: str,
        list_idx_player: List[int],
        except_idx: Union[None, int, List[int]] = None,
        do_log: bool = True,
    ):
        """Add a message to the observation of specific players."""
        list_idx_player = self.exclude_except(list_idx_player, except_idx)
        for idx_player in list_idx_player:
            self.add_message(text, idx_player, do_log=False)
        # Log the message
        if self.do_log_messages and do_log:
            self.logger.info(f"[MESSAGE] Message specific to {list_idx_player} : {text}")

    def add_global_message(
        self, text: str, except_idx: Union[None, int, List[int]] = None, do_log: bool = True
    ):
        """Add a message to the observation of all players (eventually except some)"""
        except_list = self.exclude_except(list(range(self.n_players)), except_idx)
        for idx_player in except_list:
            self.add_message(text, idx_player, do_log=False)
        # Log the message
        if self.do_log_messages and do_log:
            if except_idx is None or (
                isinstance(except_idx, list) and len(except_idx) == 0
            ):
                self.logger.info(f"[MESSAGE] Message global : {text}")
            else:
                self.logger.info(f"[MESSAGE] Message global except {except_list} : {text}")

    def reset(self, idx_player: int):
        """Reset to empty the observation of a player."""
        self[idx_player] = ""

    def reset_global(self):
        """Reset to empty the observation of all players."""
        for i in range(self.n_players):
            self.reset(i)

    # ==== Helper methods ====
    def __repr__(self) -> str:
        list_obs = [f"Player {i} obs: \n{self[i]}" for i in range(self.n_players)]
        return "\nCommon Obs :\n" + "\n\n".join(list_obs)

    def exclude_except(
        self, list_idx_player: List[int], except_idx: Union[None, int, List[int]]
    ):
        if except_idx is None:
            return list_idx_player
        elif isinstance(except_idx, int):
            return [idx for idx in list_idx_player if idx != except_idx]
        elif isinstance(except_idx, list):
            return [idx for idx in list_idx_player if idx not in except_idx]
        else:
            raise ValueError("except_idx must be None, int or list of int")

    def log(self, text: str, indicator : str = "INFO"):
        """Log a message to the logger if logging is enabled.

        Args:
            text (str): The message to log.
        """
        if self.do_log_infos:
            self.logger.info(f"[{indicator}] {text}")
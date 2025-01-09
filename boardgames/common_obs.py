from typing import Dict, List, Optional, Tuple, Union


class CommonObs(list):
    def __init__(self, text: Optional[str] = "", n_players: int = 5) -> None:
        self.n_players = n_players
        super().__init__([text for _ in range(n_players)])

    def add_message(self, text: str, idx_player: int):
        if self[idx_player] in ["", None]:
            self[idx_player] = text
        else:
            self[idx_player] += f"\n{text}"

    def add_specific_message(
        self,
        text: str,
        list_idx_player: List[int],
        except_idx: Union[None, int, List[int]] = None,
    ):
        except_list = except_idx if isinstance(except_idx, list) else [except_idx]
        for idx_player in list_idx_player:
            if not (idx_player in except_list):
                self.add_message(text, idx_player)

    def add_global_message(
        self, text: str, except_idx: Union[None, int, List[int]] = None
    ):
        except_list = except_idx if isinstance(except_idx, list) else [except_idx]
        for idx_player in range(self.n_players):
            if not (idx_player in except_list):
                self.add_message(text, idx_player)

    def reset(self, idx_player: int):
        self[idx_player] = ""

    def reset_global(self):
        for i in range(self.n_players):
            self.reset(i)

    def __repr__(self) -> str:
        list_obs = [f"Player {i} obs: \n{self[i]}" for i in range(self.n_players)]
        return "\nCommon Obs :\n" + "\n\n".join(list_obs)

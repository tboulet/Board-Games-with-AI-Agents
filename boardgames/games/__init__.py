from typing import Dict, Type
from boardgames.games.base_game import BaseGame
from boardgames.games.secret_hitler import SecretHitlerGame
from boardgames.games.times_bomb import TimesBomb


game_name_to_GameClass: Dict[str, Type[BaseGame]] = {
    "SecretHitler": SecretHitlerGame,
    "TimesBomb": TimesBomb,
}

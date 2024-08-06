from typing import Dict, Type
from boardgames.games.base_game import BaseGame
from boardgames.games.secret_hitler import SecretHitlerGame


game_name_to_GameClass: Dict[str, Type[BaseGame]] = {
    "SecretHitty": SecretHitlerGame,
}

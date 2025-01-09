from boardgames.games.werewolves.causes_of_deaths.base_cause import CauseOfDeath
from typing import List


class CauseVote(CauseOfDeath):
    def get_name(self):
        return "Vote"
    
    def is_day_cause_of_death(self):
        return True

    def get_message_on_death(self, state, id_player):
        return f"Player {id_player} was eliminated by the vote."

class CauseWolfAttack(CauseOfDeath):
    def get_name(self):
        return "Wolf attack"
    
    def is_day_cause_of_death(self):
        return False

    def get_message_on_death(self, state, id_player):
        return f"Player {id_player} was eliminated by the werewolves."
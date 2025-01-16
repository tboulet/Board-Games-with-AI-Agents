from typing import Dict, Type


from .base_role import RoleWW
from .villager import RoleVillager
from .wolf import RoleWerewolf
from .seer import RoleSeer
from .witch import RoleWitch
from .hunter import RoleHunter
from .bodyguard import RoleBodyguard

ROLES_CLASSES_WW: Dict[str, Type[RoleWW]] = {
    # Village - Ordinary roles
    RoleVillager.get_name(): RoleVillager,
    # Village - Information roles
    RoleSeer.get_name(): RoleSeer,
    # Village - Defensive roles
    RoleBodyguard.get_name(): RoleBodyguard,
    # Village - Offensive roles
    RoleWitch.get_name(): RoleWitch,
    RoleHunter.get_name(): RoleHunter,
    # Werewolves
    RoleWerewolf.get_name(): RoleWerewolf,
}

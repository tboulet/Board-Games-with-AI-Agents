from typing import Dict, Type


from .base_role import RoleWW
from .villager import RoleVillager
from .wolf import RoleWerewolf
from .seer import RoleSeer
from .witch import RoleWitch
from .hunter import RoleHunter
from .bodyguard import RoleBodyguard
from .angel import RoleAngel
from .wild_child import RoleWildChild
from .elder import RoleElder
from .village_fool import RoleVillageFool

ROLES_CLASSES_WW: Dict[str, Type[RoleWW]] = {
    # Village - Ordinary roles
    RoleVillager.get_name(): RoleVillager,
    # Village - Information roles
    RoleSeer.get_name(): RoleSeer,
    # Village - Defensive roles
    RoleBodyguard.get_name(): RoleBodyguard,
    RoleElder.get_name(): RoleElder,
    RoleVillageFool.get_name(): RoleVillageFool,
    # Village - Offensive roles
    RoleWitch.get_name(): RoleWitch,
    RoleHunter.get_name(): RoleHunter,
    # Werewolves
    RoleWerewolf.get_name(): RoleWerewolf,
    # Hybrid roles
    RoleAngel.get_name(): RoleAngel,
    RoleWildChild.get_name(): RoleWildChild,    
}

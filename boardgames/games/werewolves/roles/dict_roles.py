from typing import Dict, Type

from .base_role import RoleWW
from .villager import RoleVillager
from .wolf import RoleWerewolf

ROLES_CLASSES_WW: Dict[str, Type[RoleWW]] = {
    RoleVillager.get_name(): RoleVillager,
    RoleWerewolf.get_name(): RoleWerewolf,
}
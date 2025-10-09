from click import group

from .create import create
from .delete import delete
from .get import get
from .get_all import get_all
from .handler import handler
from .update import update
from .security import security


@group()
def solutions():
    """Solutions - Cosmotech API"""
    pass


list_commands = [delete, get_all, create, get, update]

for _command in list_commands:
    solutions.add_command(_command)

list_groups = [handler, security]

for _group in list_groups:
    solutions.add_command(_group)

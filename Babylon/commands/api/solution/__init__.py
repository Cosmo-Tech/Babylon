from click import group

from .handler import handler
from .create import create
from .delete import delete
from .get import get
from .get_all import get_all
from .get_current import get_current
from .update import update


@group()
def solution():
    """Subgroup handling Solution in the cosmotech API"""
    pass


list_commands = [
    delete,
    get_current,
    get_all,
    create,
    get,
    update,
]

for _command in list_commands:
    solution.add_command(_command)

list_groups = [
    handler,
]

for _group in list_groups:
    solution.add_command(_group)

from click import group

from .handler import handler
from .create import create
from .delete import delete
from .get import get
from .get_all import get_all
from .update import update
from .delete_all import delete_all


@group()
def solution():
    """Subgroup handling Solution in the cosmotech API"""
    pass


list_commands = [
    delete,
    get_all,
    create,
    get,
    update,
    delete_all
]

for _command in list_commands:
    solution.add_command(_command)

list_groups = [
    handler,
]

for _group in list_groups:
    solution.add_command(_group)

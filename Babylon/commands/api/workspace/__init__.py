from click import group

from .create import create
from .delete import delete
from .get import get
from .get_all import get_all
from .security import security
from .update import update
from .delete_all import delete_all

list_commands = [
    update,
    delete,
    get_all,
    get,
    create,
    delete_all
]


@group()
def workspace():
    """Subgroup handling Work in the cosmotech API"""
    pass


for _command in list_commands:
    workspace.add_command(_command)

list_groups = [
    security,
]

for _group in list_groups:
    workspace.add_command(_group)

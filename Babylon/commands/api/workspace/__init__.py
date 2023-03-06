from click import group

from .create import create
from .delete import delete
from .get import get
from .get_all import get_all
from .get_current import get_current
from .update import update

list_commands = [
    get_current,
    update,
    delete,
    get_all,
    get,
    create,
]


@group()
def workspace():
    """Subgroup handling Work in the cosmotech API"""
    pass


for _command in list_commands:
    workspace.add_command(_command)

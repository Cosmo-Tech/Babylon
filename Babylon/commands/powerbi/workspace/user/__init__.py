from click import group

from .get_all import get_all
from .add import add
from .update import update
from .delete import delete

list_commands = [
    get_all,
    add,
    update,
    delete,
]


@group()
def user():
    """Subgroup allowing control of the users and their access to the workspace"""
    pass


for _command in list_commands:
    user.add_command(_command)

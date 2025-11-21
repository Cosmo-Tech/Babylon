from click import group

from .add import add
from .delete import delete
from .get_all import get_all
from .update import update

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

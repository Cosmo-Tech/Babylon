from click import group

from .create import create
from .delete import delete
from .get import get
from .get_all import get_all
from .update import update

list_commands = [
    create,
    delete,
    get_all,
    get,
    update,
]


@group()
def vars():
    """Interact with the vars of a workspace"""
    pass


for _command in list_commands:
    vars.add_command(_command)

from click import group

from .list import list
from .delete import delete
from .create import create
from .run import run

list_commands = [
    list,
    delete,
    create,
    run,
]


@group()
def arm():
    """Group interacting with Azure Resources Manager"""
    pass


for _command in list_commands:
    arm.add_command(_command)

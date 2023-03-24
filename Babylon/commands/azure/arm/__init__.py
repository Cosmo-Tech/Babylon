from click import group

from .get_all import get_all
from .delete import delete
from .create import create
from .run import run

list_commands = [
    get_all,
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

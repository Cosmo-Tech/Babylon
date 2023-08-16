from click import group
from .get_all import get_all
from .run import run

list_commands = [
    get_all,
    run,
]


@group()
def arm():
    """Azure Resources Manager"""
    pass


for _command in list_commands:
    arm.add_command(_command)

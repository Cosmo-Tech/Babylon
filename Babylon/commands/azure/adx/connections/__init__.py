from click import group

from Babylon.utils.decorators import wrapcontext
from .create import create

list_commands = [
    create,
]


@group(name="connections")
@wrapcontext()
def connections_group():
    """ADX database DataConnections"""
    pass


for _command in list_commands:
    connections_group.add_command(_command)

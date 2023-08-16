from click import group

from .create import create

list_commands = [
    create,
]


@group(name="connections")
def connections_group():
    """ADX database DataConnections"""
    pass


for _command in list_commands:
    connections_group.add_command(_command)

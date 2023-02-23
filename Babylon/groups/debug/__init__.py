from click import group

from .commands import list_commands


@group()
def debug():
    """Add debug capacities of runs"""


for _command in list_commands:
    debug.add_command(_command)

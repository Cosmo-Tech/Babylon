from click import group

from .commands import list_commands
from .groups import list_groups


@group(hidden=True)
def dev():
    """Command group used to simplify some development operations"""


for _command in list_commands:
    dev.add_command(_command)


for _command in list_groups:
    dev.add_command(_command)

from click import group

from .commands import list_commands
from .groups import list_groups


@group()
def permission():
    """Group interacting with ADX permissions"""
    pass


for _command in list_commands:
    permission.add_command(_command)

for _group in list_groups:
    permission.add_command(_group)
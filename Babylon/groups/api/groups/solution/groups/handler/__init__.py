from click import group

from .commands import list_commands
from .groups import list_groups


@group()
def handler():
    """Group allowing solution handler management"""
    pass


for _command in list_commands:
    handler.add_command(_command)

for _group in list_groups:
    handler.add_command(_group)

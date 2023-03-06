from click import group

from .commands import list_commands
from .groups import list_groups


@group()
def group():
    """Group interacting with Azure Directory Groups"""
    pass


for _command in list_commands:
    group.add_command(_command)

for _group in list_groups:
    group.add_command(_group)

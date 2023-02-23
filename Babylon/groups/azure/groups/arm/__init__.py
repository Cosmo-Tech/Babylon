from click import group

from .commands import list_commands
from .groups import list_groups


@group()
def arm():
    """Group interacting with Azure Resources Manager"""
    pass


for _command in list_commands:
    arm.add_command(_command)

for _group in list_groups:
    arm.add_command(_group)

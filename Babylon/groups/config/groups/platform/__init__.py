from click import group

from .commands import list_commands
from .groups import list_groups


@group()
def platform():
    """Sub-group for platform"""
    pass


for _command in list_commands:
    platform.add_command(_command)

for _group in list_groups:
    platform.add_command(_group)

from click import group

from .commands import list_commands
from .groups import list_groups


@group()
def adx():
    """Group interacting with Azure Data Explorer"""
    pass


for _command in list_commands:
    adx.add_command(_command)

for _group in list_groups:
    adx.add_command(_group)

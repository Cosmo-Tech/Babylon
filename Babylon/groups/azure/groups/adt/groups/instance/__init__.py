from click import group

from .commands import list_commands
from .groups import list_groups


@group()
def instance():
    """Subgroup dedicate to Azure digital twins instance management"""
    pass


for _command in list_commands:
    instance.add_command(_command)

for _group in list_groups:
    instance.add_command(_group)

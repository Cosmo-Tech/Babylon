from click import group

from .commands import list_commands
from .groups import list_groups


@group()
def model():
    """Subgroup dedicate to Azure digital twins models management"""
    pass


for _command in list_commands:
    model.add_command(_command)

for _group in list_groups:
    model.add_command(_group)

from click import group

from .commands import list_commands
from .groups import list_groups


@group()
def user():
    """Subgroup allowing control of the users and their access to the workspace"""
    pass


for _command in list_commands:
    user.add_command(_command)

for _group in list_groups:
    user.add_command(_group)

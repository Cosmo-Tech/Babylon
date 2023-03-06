from click import group

from .commands import list_commands
from .groups import list_groups


@group()
def password():
    """Group interactiving with app registration passwords and secrets"""
    pass


for _command in list_commands:
    password.add_command(_command)

for _group in list_groups:
    password.add_command(_group)

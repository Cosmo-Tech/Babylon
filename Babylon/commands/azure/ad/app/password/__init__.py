from click import group

from .delete import delete
from .create import create

list_commands = [delete, create]


@group()
def password():
    """Group interactiving with app registration passwords and secrets"""
    pass


for _command in list_commands:
    password.add_command(_command)

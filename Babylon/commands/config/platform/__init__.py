from click import group

from .create import create
from .edit import edit
from .select import select

list_commands = [create, edit, select]


@group()
def platform():
    """Sub-group for platform"""
    pass


for _command in list_commands:
    platform.add_command(_command)

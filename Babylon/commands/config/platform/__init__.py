from click import group

from .create import create
from .edit import edit

list_commands = [
    create,
    edit
]


@group()
def platform():
    """Sub-group for platform"""
    pass


for _command in list_commands:
    platform.add_command(_command)

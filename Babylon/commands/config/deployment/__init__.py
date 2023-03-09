from click import group

from .create import create
from .edit import edit

list_commands = [
    create,
    edit
]


@group()
def deployment():
    """Sub-group for deployment"""
    pass


for _command in list_commands:
    deployment.add_command(_command)

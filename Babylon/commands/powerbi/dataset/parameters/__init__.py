from click import group

from .get import get
from .update import update

list_commands = [
    get,
    update,
]


@group()
def parameters():
    """Command group handling PowerBI dataset parameters"""
    pass


for _command in list_commands:
    parameters.add_command(_command)

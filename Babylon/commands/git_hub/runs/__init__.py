from click import group

from .cancel import cancel
from .get import get

list_commands = [get, cancel]


@group()
def runs():
    """github workflows runs"""
    pass


for _command in list_commands:
    runs.add_command(_command)

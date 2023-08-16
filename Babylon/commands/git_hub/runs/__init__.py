from click import group
from .get import get
from .cancel import cancel

list_commands = [get, cancel]


@group()
def runs():
    """github workflows runs"""
    pass


for _command in list_commands:
    runs.add_command(_command)

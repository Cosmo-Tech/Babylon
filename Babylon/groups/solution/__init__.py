from click import group

from .commands import list_commands


@group()
def solution():
    """Command group handling local solution information"""


for _command in list_commands:
    solution.add_command(_command)

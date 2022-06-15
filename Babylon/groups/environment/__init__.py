from click import group

from .commands import list_commands


@group()
def environment():
    """Command group handling local environment information"""


for _command in list_commands:
    environment.add_command(_command)

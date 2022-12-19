from click import group

from .commands import list_commands
from .groups import list_groups


@group()
def working_dir():
    """Command group handling working directory information"""


for _command in list_commands:
    working_dir.add_command(_command)

for _command in list_groups:
    working_dir.add_command(_command)

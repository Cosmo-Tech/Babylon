from click import group

from .commands import list_commands
from .groups import list_groups


@group()
def self():
    """Command group used to simplify some development operations"""


for _command in list_commands:
    self.add_command(_command)


for _command in list_groups:
    self.add_command(_command)

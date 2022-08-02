from click import group

from .commands import list_commands


@group()
def self():
    """Command group used to simplify some development operations"""


for _command in list_commands:
    self.add_command(_command)

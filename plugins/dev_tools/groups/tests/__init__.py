from click import group

from .commands import list_commands
from .groups import list_groups


@group()
def tests():
    """Sub group for test commands"""
    pass


for _command in list_commands:
    tests.add_command(_command)

for _group in list_groups:
    tests.add_command(_group)

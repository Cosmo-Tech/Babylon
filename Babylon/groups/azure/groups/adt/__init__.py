from click import group

from .commands import list_commands
from .groups import list_groups


@group()
def adt():
    """Allow communication with Azure Digital Twin"""


for _command in list_commands:
    adt.add_command(_command)

for _group in list_groups:
    adt.add_command(_group)

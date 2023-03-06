from click import group

from .commands import list_commands
from .groups import list_groups


@group()
def powerbi():
    """Group handling communication with PowerBI API"""


for _command in list_commands:
    powerbi.add_command(_command)

for _group in list_groups:
    powerbi.add_command(_group)

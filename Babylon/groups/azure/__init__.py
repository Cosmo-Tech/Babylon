import logging

from click import group

from .commands import list_commands
from .groups import list_groups

logger = logging.getLogger("Babylon")


@group()
def azure():
    """Group allowing communication with Microsoft Azure Cloud"""


for _command in list_commands:
    azure.add_command(_command)

for _group in list_groups:
    azure.add_command(_group)

import logging

from click import group

from .commands import list_commands
from .groups import list_groups
from .....utils.decorators import requires_external_program

logger = logging.getLogger("Babylon")


@group()
@requires_external_program("docker")
def acr():
    """Group interacting with Azure Container Registry"""


for _command in list_commands:
    acr.add_command(_command)

for _group in list_groups:
    acr.add_command(_group)

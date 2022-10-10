from click import group
from click import pass_context
from click.core import Context
from Babylon.utils.decorators import requires_external_program
from .commands import list_commands
from .groups import list_groups


@group()
@requires_external_program("docker")
@pass_context
def acr(ctx: Context):
    """Group interacting with Azure Container Registry"""

for _command in list_commands:
    acr.add_command(_command)

for _group in list_groups:
    acr.add_command(_group)

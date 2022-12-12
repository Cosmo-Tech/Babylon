import logging

from azure.identity import DefaultAzureCredential
from click import group
from click import pass_context
from click.core import Context

from ...utils.decorators import requires_external_program
from .commands import list_commands
from .groups import list_groups

logger = logging.getLogger("Babylon")


@group()
@pass_context
@requires_external_program("az")
def azure(ctx: Context):
    """Group allowing communication with Microsoft Azure Cloud"""
    ctx.obj = DefaultAzureCredential()


for _command in list_commands:
    azure.add_command(_command)

for _group in list_groups:
    azure.add_command(_group)

from azure.identity import AzureCliCredential
from azure.identity import DefaultAzureCredential
from click import group
from click import pass_context
from click.core import Context

from .commands import list_commands
from .groups import list_groups


@group()
@pass_context
def azure(ctx: Context):
    """Group allowing communication with Microsoft Azure Cloud"""
    try:
        credentials = AzureCliCredential()
    except:
        credentials = DefaultAzureCredential()
    ctx.obj = credentials


for _command in list_commands:
    azure.add_command(_command)

for _group in list_groups:
    azure.add_command(_group)

import sys

from click import group
from click import pass_context
from click.core import Context
from azure.identity import DefaultAzureCredential
from azure.core.exceptions import ClientAuthenticationError

from .commands import list_commands
from .groups import list_groups


@group()
@pass_context
def powerbi(ctx: Context):
    """Group handling communication with PowerBI API"""
    try:
        token = DefaultAzureCredential().get_token("https://analysis.windows.net/powerbi/api/.default")
    except ClientAuthenticationError:
        # Error message is handled by Azure API
        sys.exit(0)
    ctx.obj = token


for _command in list_commands:
    powerbi.add_command(_command)

for _group in list_groups:
    powerbi.add_command(_group)

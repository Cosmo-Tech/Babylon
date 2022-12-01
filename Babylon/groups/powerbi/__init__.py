import sys

from click import group
from click import pass_context
from click.core import Context
from azure.identity import DefaultAzureCredential
from azure.core.exceptions import ClientAuthenticationError

from .commands import list_commands
from .groups import list_groups
from ...utils.decorators import require_platform_key


@group()
@pass_context
@require_platform_key("powerbi_api_scope")
def powerbi(ctx: Context, powerbi_api_scope: str):
    """Group handling communication with PowerBI API"""
    try:
        token = DefaultAzureCredential().get_token(powerbi_api_scope)
    except ClientAuthenticationError:
        # Error message is handled by Azure API
        sys.exit(0)
    ctx.obj = token


for _command in list_commands:
    powerbi.add_command(_command)

for _group in list_groups:
    powerbi.add_command(_group)

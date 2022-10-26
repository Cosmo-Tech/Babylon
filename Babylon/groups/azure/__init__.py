import logging
import sys

from azure.core.exceptions import ClientAuthenticationError
from azure.identity import DefaultAzureCredential
from click import group
from click import pass_context
from click.core import Context

from Babylon.utils.decorators import require_platform_key
from .commands import list_commands
from .groups import list_groups

logger = logging.getLogger("Babylon")


@group()
@pass_context
@require_platform_key("api_scope", "api_scope")
def azure(ctx: Context, api_scope: str):
    """Group allowing communication with Microsoft Azure Cloud"""
    creds = DefaultAzureCredential()
    try:
        # Authentication fails only when token can't be retrieved
        creds.get_token(api_scope)
        ctx.obj = creds
    except ClientAuthenticationError:
        logger.error("Please login to azure CLI with `az login`")
        sys.exit(1)


for _command in list_commands:
    azure.add_command(_command)

for _group in list_groups:
    azure.add_command(_group)

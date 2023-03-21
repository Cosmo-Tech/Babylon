import sys

import cosmotech_api
from azure.core.exceptions import ClientAuthenticationError
from azure.identity import DefaultAzureCredential
from click import group
from click import pass_context
from click.core import Context

from .commands import list_commands
from .groups import list_groups
from ...utils.decorators import require_platform_key


@group()
@pass_context
@require_platform_key("api_scope", "api_scope")
@require_platform_key("api_url", "api_url")
def api(ctx: Context, api_scope: str, api_url: str):
    """Group handling communication with the cosmotech API"""
    try:
        token = DefaultAzureCredential(exclude_shared_token_cache_credential=True).get_token(api_scope)
    except ClientAuthenticationError:
        # Error message is handled by Azure API
        sys.exit(0)

    configuration = cosmotech_api.Configuration(host=api_url, discard_unknown_keys=True, access_token=token.token)

    ctx.obj = configuration


for _command in list_commands:
    api.add_command(_command)

for _group in list_groups:
    api.add_command(_group)

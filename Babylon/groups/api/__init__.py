import cosmotech_api
from click import group
from click import pass_context
from click.core import Context

from .commands import list_commands
from .groups import list_groups
from ...utils.decorators import require_platform_key
from ...utils.decorators import pass_azure_token


@group()
@pass_context
@require_platform_key("api_url")
@pass_azure_token("csm_api")
def api(ctx: Context, api_url: str, azure_token):
    """Group handling communication with the cosmotech API"""
    configuration = cosmotech_api.Configuration(host=api_url,
                                                discard_unknown_keys=True,
                                                access_token=azure_token)
    ctx.obj = configuration


for _command in list_commands:
    api.add_command(_command)

for _group in list_groups:
    api.add_command(_group)

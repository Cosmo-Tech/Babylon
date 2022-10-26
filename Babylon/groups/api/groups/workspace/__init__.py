from click import group
from click import pass_context
from click.core import Context
from cosmotech_api import ApiClient
from cosmotech_api.api.workspace_api import WorkspaceApi

from Babylon.utils.decorators import pass_api_configuration
from .commands import list_commands
from .groups import list_groups


@group()
@pass_api_configuration
@pass_context
def workspace(ctx: Context, api_configuration):
    """Subgroup handling Work in the cosmotech API"""
    api_client = ApiClient(api_configuration)
    ctx.obj = WorkspaceApi(api_client)


for _command in list_commands:
    workspace.add_command(_command)

for _group in list_groups:
    workspace.add_command(_group)

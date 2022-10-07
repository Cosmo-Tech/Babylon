import cosmotech_api
from click import group, pass_context
from click.core import Context
from cosmotech_api.api.connector_api import ConnectorApi

from .....utils.decorators import pass_api_configuration
from .commands import list_commands
from .groups import list_groups


@group()
@pass_api_configuration
@pass_context
def connector(ctx: Context, api_configuration):
    """Subgroup handling Connectors in the cosmotech API"""
    api_client = cosmotech_api.ApiClient(api_configuration)
    ctx.obj = ConnectorApi(api_client)


for _command in list_commands:
    connector.add_command(_command)

for _group in list_groups:
    connector.add_command(_group)

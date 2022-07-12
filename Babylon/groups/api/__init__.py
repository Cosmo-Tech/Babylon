import cosmotech_api
from azure.identity import AzureCliCredential
from azure.identity import DefaultAzureCredential
from click import group
from click import pass_context
from click.core import Context

from .commands import list_commands
from .groups import list_groups
from ...utils.decorators import env_requires_yaml_key


@group()
@pass_context
@env_requires_yaml_key("deploy.yaml", "api_scope", "api_scope")
@env_requires_yaml_key("deploy.yaml", "api_url", "api_url")
def api(ctx: Context, api_scope: str, api_url: str):
    """Group handling communication with the cosmotech API"""
    try:
        credentials = AzureCliCredential()
    except:
        credentials = DefaultAzureCredential()

    token = credentials.get_token(api_scope)
    configuration = cosmotech_api.Configuration(
        host=api_url,
        discard_unknown_keys=True,
        access_token=token.token
    )

    ctx.obj = configuration


for _command in list_commands:
    api.add_command(_command)

for _group in list_groups:
    api.add_command(_group)

import sys

from azure.identity import DefaultAzureCredential
from azure.core.exceptions import ClientAuthenticationError
from click import group
from click import pass_context
from click.core import Context

from .commands import list_commands
from .groups import list_groups


@group()
@pass_context
def appinsight(ctx: Context):
    """Group interacting with Azure App Insight"""
    credentials = ctx.find_object(DefaultAzureCredential)
    try:
        token = credentials.get_token("https://management.azure.com/.default")
    except ClientAuthenticationError:
        # Error message is handled by Azure API
        sys.exit(0)
    ctx.obj = token


for _command in list_commands:
    appinsight.add_command(_command)

for _group in list_groups:
    appinsight.add_command(_group)

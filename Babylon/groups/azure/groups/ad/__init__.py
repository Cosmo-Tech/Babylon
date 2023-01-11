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
def ad(ctx: Context):
    """Group interacting with Azure Active Directory"""
    credentials = ctx.find_object(DefaultAzureCredential)
    try:
        token = credentials.get_token("https://graph.microsoft.com/.default")
    except ClientAuthenticationError:
        # Error message is handled by Azure API
        sys.exit(0)
    ctx.obj = token

for _command in list_commands:
    ad.add_command(_command)

for _group in list_groups:
    ad.add_command(_group)

from click import group
from click import pass_context
from click.core import Context

from azure.mgmt.digitaltwins import AzureDigitalTwinsManagementClient

from .......utils.decorators import require_platform_key
from .commands import list_commands
from .groups import list_groups


@group()
@pass_context
@require_platform_key("azure_subscription", "azure_subscription")
def instance(ctx: Context, azure_subscription: str):
    """Group initialized from a template"""
    _credential = ctx.parent.obj
    ctx.obj = AzureDigitalTwinsManagementClient(_credential, azure_subscription)


for _command in list_commands:
    instance.add_command(_command)

for _group in list_groups:
    instance.add_command(_group)
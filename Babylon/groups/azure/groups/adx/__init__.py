from azure.mgmt.kusto import KustoManagementClient
from click import group

from .commands import list_commands
from .groups import list_groups
from .....utils.decorators import require_platform_key


@group()
@pass_context
@require_platform_key("azure_subscription", "azure_subscription")
def adx(ctx: Context, azure_subscription: str):
    """Group interacting with Azure Data Explorer"""
    ctx.obj = KustoManagementClient(credential=ctx.parent.obj,
                                    subscription_id=azure_subscription)


for _command in list_commands:
    adx.add_command(_command)

for _group in list_groups:
    adx.add_command(_group)

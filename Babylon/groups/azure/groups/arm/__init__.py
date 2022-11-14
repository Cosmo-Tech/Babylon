from click import group
from click import pass_context
from click.core import Context
from azure.mgmt.resource import ResourceManagementClient

from .....utils.decorators import require_platform_key
from .commands import list_commands
from .groups import list_groups


@group()
@pass_context
@require_platform_key("azure_subscription", "azure_subscription")
def arm(ctx: Context, azure_subscription: str):
    """Group initialized from a template"""
    ctx.obj = ResourceManagementClient(credential=ctx.parent.obj, subscription_id=azure_subscription)


for _command in list_commands:
    arm.add_command(_command)

for _group in list_groups:
    arm.add_command(_group)

from azure.digitaltwins.core import DigitalTwinsClient
from click import group
from click import pass_context
from click.core import Context

from .commands import list_commands
from .groups import list_groups
from .....utils.decorators import require_deployment_key


@group()
@pass_context
@require_deployment_key("digital_twin_url", "digital_twin_url")
def adt(ctx: Context, digital_twin_url: str):
    """Allow communication with Azure Digital Twin"""

    ctx.obj = DigitalTwinsClient(credential=ctx.parent.obj,
                                 endpoint=digital_twin_url)


for _command in list_commands:
    adt.add_command(_command)

for _group in list_groups:
    adt.add_command(_group)

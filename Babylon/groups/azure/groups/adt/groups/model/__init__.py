from click import group
from click import pass_context
from click.core import Context
from azure.digitaltwins.core import DigitalTwinsClient

from .......utils.decorators import require_deployment_key

from .commands import list_commands
from .groups import list_groups


@group()
@pass_context
@require_deployment_key("digital_twin_url", "digital_twin_url")
def model(ctx: Context, digital_twin_url: str):
    """Subgroup dedicate to Azure digital twins models management"""
    ctx.obj = DigitalTwinsClient(credential=ctx.parent.obj, endpoint=digital_twin_url)


for _command in list_commands:
    model.add_command(_command)

for _group in list_groups:
    model.add_command(_group)

from click import group
from click import pass_context
from click.core import Context
from .commands import list_commands
from .groups import list_groups


@group()
@pass_context
def acr(ctx: Context):
    """Nothing needed here"""

for _command in list_commands:
    acr.add_command(_command)

for _group in list_groups:
    acr.add_command(_group)

from click import group
from click import pass_context
from click.core import Context

from .commands import list_commands
from .groups import list_groups

@group()
@pass_context
def adt(ctx: Context):
    """Allow communication with Azure Digital Twin"""
    ctx.obj = ctx.parent.obj


for _command in list_commands:
    adt.add_command(_command)

for _group in list_groups:
    adt.add_command(_group)

from click import group
from click import pass_context
from click.core import Context

from .commands import list_commands
from .groups import list_groups


@group()
@pass_context
def permission(ctx: Context):
    """Group interacting with ADX permissions"""
    pass


for _command in list_commands:
    permission.add_command(_command)

for _group in list_groups:
    permission.add_command(_group)
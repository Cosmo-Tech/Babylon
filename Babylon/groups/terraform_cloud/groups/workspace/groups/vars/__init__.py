from click import group
from click import pass_context
from click.core import Context

from .commands import list_commands
from .groups import list_groups


@group()
@pass_context
def vars(ctx: Context):
    """Interact with the vars of a workspace"""
    pass


for _command in list_commands:
    vars.add_command(_command)

for _group in list_groups:
    vars.add_command(_group)
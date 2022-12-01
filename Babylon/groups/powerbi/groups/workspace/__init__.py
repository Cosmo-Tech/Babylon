from click import group
from click import pass_context
from click.core import Context

from .commands import list_commands
from .groups import list_groups


@group()
@pass_context
def workspace(ctx: Context):
    """Group initialized from a template"""
    pass


for _command in list_commands:
    workspace.add_command(_command)

for _group in list_groups:
    workspace.add_command(_group)

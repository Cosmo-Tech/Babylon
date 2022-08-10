from click import group
from click import pass_context
from click.core import Context

from .commands import list_commands
from .groups import list_groups


@group()
@pass_context
def deployment(ctx: Context):
    """Sub-group for deployment"""
    pass


for _command in list_commands:
    deployment.add_command(_command)

for _group in list_groups:
    deployment.add_command(_group)
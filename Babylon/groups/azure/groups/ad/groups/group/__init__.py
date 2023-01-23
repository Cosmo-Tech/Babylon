from click import group
from click import pass_context
from click.core import Context

from .commands import list_commands
from .groups import list_groups


@group()
@pass_context
def group(ctx: Context):
    """Group interacting with Azure Directory Groups"""
    pass


for _command in list_commands:
    group.add_command(_command)

for _group in list_groups:
    group.add_command(_group)

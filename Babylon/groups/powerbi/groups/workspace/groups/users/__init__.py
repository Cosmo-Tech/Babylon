from click import group
from click import pass_context
from click.core import Context

from .commands import list_commands
from .groups import list_groups


@group()
@pass_context
def users(ctx: Context):
    """Subgroup allowing control of the users and their access to the workspace"""
    pass


for _command in list_commands:
    users.add_command(_command)

for _group in list_groups:
    users.add_command(_group)

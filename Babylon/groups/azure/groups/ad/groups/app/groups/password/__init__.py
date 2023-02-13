from click import group
from click import pass_context
from click.core import Context

from .commands import list_commands
from .groups import list_groups


@group()
@pass_context
def password(ctx: Context):
    """Group interactiving with app registration passwords and secrets"""
    pass


for _command in list_commands:
    password.add_command(_command)

for _group in list_groups:
    password.add_command(_group)

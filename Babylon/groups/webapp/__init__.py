from click import group
from click import pass_context
from click.core import Context

from .commands import list_commands
from .groups import list_groups


@group()
@pass_context
def webapp(ctx: Context):
    """Group handling Cosmo Sample WebApp configuration"""
    pass


for _command in list_commands:
    webapp.add_command(_command)

for _group in list_groups:
    webapp.add_command(_group)

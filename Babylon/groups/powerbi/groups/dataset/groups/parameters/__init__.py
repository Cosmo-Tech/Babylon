from click import group
from click import pass_context
from click.core import Context

from .commands import list_commands
from .groups import list_groups


@group()
@pass_context
def parameters(ctx: Context):
    """Group initialized from a template"""
    pass


for _command in list_commands:
    parameters.add_command(_command)

for _group in list_groups:
    parameters.add_command(_group)

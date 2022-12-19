from click import group
from click import pass_context
from click.core import Context

from .commands import list_commands
from .groups import list_groups


@group()
@pass_context
def dataset(ctx: Context):
    """Command group handling PowerBI datasets"""
    pass


for _command in list_commands:
    dataset.add_command(_command)

for _group in list_groups:
    dataset.add_command(_group)

from click import group
from click import pass_context
from click.core import Context

from .commands import list_commands
from .groups import list_groups


@group()
@pass_context
def container(ctx: Context):
    """Group interacting with Azure Storage Blob containers"""
    pass


for _command in list_commands:
    container.add_command(_command)

for _group in list_groups:
    container.add_command(_group)

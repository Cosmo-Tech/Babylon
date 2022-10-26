from click import group
from click import pass_context
from click.core import Context

from .commands import list_commands
from .groups import list_groups


@group()
@pass_context
def workspace(ctx: Context):
    """Sub-group allowing interaction with the organization of the Terraform Cloud API"""
    pass


for _command in list_commands:
    workspace.add_command(_command)

for _group in list_groups:
    workspace.add_command(_group)

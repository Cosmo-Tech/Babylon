from click import group
from click import pass_context
from click.core import Context

from .commands import list_commands
from .groups import list_groups


@group()
@pass_context
def datasource(ctx: Context):
    """Command group handling PowerBI dataset datasources"""
    pass


for _command in list_commands:
    datasource.add_command(_command)

for _group in list_groups:
    datasource.add_command(_group)

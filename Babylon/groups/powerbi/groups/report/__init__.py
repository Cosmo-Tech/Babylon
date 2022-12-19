from click import group
from click import pass_context
from click.core import Context

from .commands import list_commands
from .groups import list_groups


@group()
@pass_context
def report(ctx: Context):
    """Command group handling PowerBI reports"""
    pass


for _command in list_commands:
    report.add_command(_command)

for _group in list_groups:
    report.add_command(_group)

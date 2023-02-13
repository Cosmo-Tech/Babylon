from click import group
from click import pass_context
from click.core import Context

from .commands import list_commands
from .groups import list_groups


@group()
@pass_context
def app(ctx: Context):
    """Group interacting with Azure Active Directory Apps"""
    pass


for _command in list_commands:
    app.add_command(_command)

for _group in list_groups:
    app.add_command(_group)

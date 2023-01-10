from click import group
from click import pass_context
from click.core import Context

from .commands import list_commands
from .groups import list_groups


@group()
@pass_context
def custom_domain(ctx: Context):
    """Group interacting with Azure Static Webapps custom domains"""
    pass


for _command in list_commands:
    custom_domain.add_command(_command)

for _group in list_groups:
    custom_domain.add_command(_group)

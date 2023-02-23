from click import group

from .commands import list_commands
from .groups import list_groups


@group()
def custom_domain():
    """Group interacting with Azure Static Webapps custom domains"""
    pass


for _command in list_commands:
    custom_domain.add_command(_command)

for _group in list_groups:
    custom_domain.add_command(_group)

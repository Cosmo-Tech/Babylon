from click import group

from .commands import list_commands
from .groups import list_groups


@group()
def staticwebapp():
    """Group interacting with Azure Static Webapps"""


for _command in list_commands:
    staticwebapp.add_command(_command)

for _group in list_groups:
    staticwebapp.add_command(_group)

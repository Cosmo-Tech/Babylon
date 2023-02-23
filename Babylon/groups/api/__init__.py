from click import group

from .commands import list_commands
from .groups import list_groups


@group()
def api():
    """Group handling communication with the cosmotech API"""
    pass


for _command in list_commands:
    api.add_command(_command)

for _group in list_groups:
    api.add_command(_group)

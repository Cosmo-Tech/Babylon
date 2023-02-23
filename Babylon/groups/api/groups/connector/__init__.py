from click import group

from .commands import list_commands
from .groups import list_groups


@group()
def connector():
    """Subgroup handling Connectors in the cosmotech API"""
    pass


for _command in list_commands:
    connector.add_command(_command)

for _group in list_groups:
    connector.add_command(_group)

from click import group

from .commands import list_commands
from .groups import list_groups


@group()
def organization():
    """Subgroup handling Organizations in the cosmotech API"""
    pass


for _command in list_commands:
    organization.add_command(_command)

for _group in list_groups:
    organization.add_command(_group)

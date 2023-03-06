from click import group

from .commands import list_commands
from .groups import list_groups


@group()
def dataset():
    """Subgroup handling Datasets in the cosmotech API"""
    pass


for _command in list_commands:
    dataset.add_command(_command)

for _group in list_groups:
    dataset.add_command(_group)

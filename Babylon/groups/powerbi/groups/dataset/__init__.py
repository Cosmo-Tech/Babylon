from click import group

from .commands import list_commands
from .groups import list_groups


@group()
def dataset():
    """Command group handling PowerBI datasets"""
    pass


for _command in list_commands:
    dataset.add_command(_command)

for _group in list_groups:
    dataset.add_command(_group)

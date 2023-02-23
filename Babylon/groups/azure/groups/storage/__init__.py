from click import group

from .commands import list_commands
from .groups import list_groups


@group()
def storage():
    """Group interacting with Azure Storage Blob"""
    pass


for _command in list_commands:
    storage.add_command(_command)

for _group in list_groups:
    storage.add_command(_group)

from click import group
from .create import create
from .delete import delete

list_commands = [create, delete]


@group()
def policy():
    """Azure Storage Blob Default Policy"""
    pass


for _command in list_commands:
    policy.add_command(_command)

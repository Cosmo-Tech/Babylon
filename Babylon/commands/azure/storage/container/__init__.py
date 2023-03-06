from click import group

from .create import create
from .delete import delete
from .get_all import get_all

list_commands = [
    delete,
    create,
    get_all,
]


@group()
def container():
    """Group interacting with Azure Storage Blob containers"""
    pass


for _command in list_commands:
    container.add_command(_command)

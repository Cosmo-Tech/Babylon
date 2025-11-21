from click import group

from .create import create
from .delete import delete
from .get_all import get_all
from .upload import upload

list_commands = [delete, create, get_all, upload]


@group()
def container():
    """Azure Storage Blob containers"""
    pass


for _command in list_commands:
    container.add_command(_command)

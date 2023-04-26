from click import group

from .create import create
from .delete import delete
from .get import get

list_commands = [create, delete, get]


@group()
def database():
    """Group interacting with Azure Data Explorer"""
    pass


for _command in list_commands:
    database.add_command(_command)

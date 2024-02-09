from click import group
from .create import create
from .delete import delete
from .get import get
from .get_all import get_all

list_commands = [delete, get_all, get, create]


@group()
def connectors():
    """Connectors - Cosmotech API"""
    pass


for _command in list_commands:
    connectors.add_command(_command)

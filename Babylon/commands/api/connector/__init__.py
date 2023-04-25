from click import group

from .create import create
from .delete import delete
from .get import get
from .get_all import get_all
from .delete_all import delete_all

list_commands = [delete, get_all, get, create, delete_all]


@group()
def connector():
    """Subgroup handling Connectors in the cosmotech API"""
    pass


for _command in list_commands:
    connector.add_command(_command)

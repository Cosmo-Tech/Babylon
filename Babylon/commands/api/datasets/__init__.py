from click import group
from .create import create
from .delete import delete
from .get import get
from .get_all import get_all
from .update import update
from .search import search
from .payload import payload

list_commands = [delete, update, get, create, search, get_all, payload]


@group()
def datasets():
    """Datasets - Cosmotech API"""
    pass


for _command in list_commands:
    datasets.add_command(_command)

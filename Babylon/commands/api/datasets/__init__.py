from click import group

from . import apply
from .create import create
from .delete import delete
from .get import get
from .get_all import get_all
from .search import search
from .security import security
from .update import update


@group()
def organizations():
    """Organizations - Cosmotech API"""
    pass


list_commands = [delete, update, get, create, search, get_all, apply]

for _command in list_commands:
    organizations.add_command(_command)

list_groups = [security]

for _group in list_groups:
    organizations.add_command(_group)

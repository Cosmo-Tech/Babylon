from click import group

from .apply import apply
from .delete import delete
from .get import get
from .get_all import get_all
from .search import search
from .security import security


@group()
def datasets():
    """Datasets - Cosmotech API"""
    pass


list_commands = [delete, get, search, get_all, apply]

for _command in list_commands:
    datasets.add_command(_command)

list_groups = [security]

for _group in list_groups:
    datasets.add_command(_group)

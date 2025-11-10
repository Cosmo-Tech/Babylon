from click import group

from .delete import delete
from .get import get
from .get_all import get_all
from .create import create
from .create_part import create_part
from .delete_part import delete_part
from .download_part import download_part
from .get_part import get_part

from .search import search
from .security import security


@group()
def datasets():
    """Datasets - Cosmotech API"""
    pass


list_commands = [delete, get, search, get_all, create, create_part, delete_part, download_part, get_part]

for _command in list_commands:
    datasets.add_command(_command)

list_groups = [security]

for _group in list_groups:
    datasets.add_command(_group)

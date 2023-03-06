from click import group

from .create import create
from .delete import delete
from .get import get
from .get_all import get_all
from .get_current import get_current
from .update import update

list_commands = [
    get_current,
    delete,
    update,
    get,
    create,
    get_all,
]


@group()
def dataset():
    """Subgroup handling Datasets in the cosmotech API"""
    pass


for _command in list_commands:
    dataset.add_command(_command)
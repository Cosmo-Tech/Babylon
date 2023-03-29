from click import group

from .create import create
from .delete import delete
from .get import get
from .get_all import get_all
from .security import security
from .update import update


@group()
def organization():
    """Subgroup handling Organizations in the cosmotech API"""
    pass


list_commands = [
    update,
    get,
    delete,
    create,
    get_all,
]

for _command in list_commands:
    organization.add_command(_command)

list_groups = [
    security,
]

for _group in list_groups:
    organization.add_command(_group)

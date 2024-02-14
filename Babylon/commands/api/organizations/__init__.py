from click import group
from .create import create
from .delete import delete
from .get import get
from .get_all import get_all
from .security import security
from .update import update
from .apply import apply


@group()
def organizations():
    """Organizations - Cosmotech API"""
    pass


list_commands = [update, get, delete, create, get_all, apply]

for _command in list_commands:
    organizations.add_command(_command)

list_groups = [
    security,
]

for _group in list_groups:
    organizations.add_command(_group)

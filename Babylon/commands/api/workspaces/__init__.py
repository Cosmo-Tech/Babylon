from click import group
from .create import create
from .delete import delete
from .get import get
from .get_all import get_all
from .security import security
from .update import update
from .send_key import send_key

list_commands = [update, delete, get_all, get, create, send_key]


@group()
def workspaces():
    """Workspaces - Cosmotech API"""
    pass


for _command in list_commands:
    workspaces.add_command(_command)

list_groups = [
    security,
]

for _group in list_groups:
    workspaces.add_command(_group)

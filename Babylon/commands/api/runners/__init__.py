from click import group

from .security import security
from .get_all import get_all
from .create import create
from .get import get
from .update import update
from .delete import delete
from .start import start

list_commands = [get_all, get, create, update, delete, start]


@group()
def runners():
    """Runners - Cosmotech API"""
    pass


for _command in list_commands:
    runners.add_command(_command)

list_groups = [security]

for _group in list_groups:
    runners.add_command(_group)

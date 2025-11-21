from click import group

from .create import create
from .delete import delete
from .get import get
from .get_all import get_all
from .security import security
from .start import start
from .stop import stop
from .update import update

list_commands = [get_all, get, create, update, delete, start, stop]


@group()
def runners():
    """Runners - Cosmotech API"""
    pass


for _command in list_commands:
    runners.add_command(_command)

list_groups = [security]

for _group in list_groups:
    runners.add_command(_group)

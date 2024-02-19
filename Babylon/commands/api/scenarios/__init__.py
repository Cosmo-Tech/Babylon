from click import group

from .apply import apply
from .security import security
from .get_all import get_all
from .create import create
from .get import get
from .update import update
from .delete import delete
from .run import run

list_commands = [get_all, get, create, update, delete, run, apply]


@group()
def scenarios():
    """Scenarios - Cosmotech API"""
    pass


for _command in list_commands:
    scenarios.add_command(_command)

list_groups = [security]

for _group in list_groups:
    scenarios.add_command(_group)

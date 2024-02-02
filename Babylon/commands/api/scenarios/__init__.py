from click import group
from .get_all import get_all
from .create import create
from .get import get
from .update import update
from .delete import delete
from .run import run

list_commands = [get_all, get, create, update, delete, run]


@group()
def scenarios():
    """Scenarios - Cosmotech API"""
    pass


for _command in list_commands:
    scenarios.add_command(_command)

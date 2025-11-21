from click import group

from .add import add
from .delete import delete
from .get import get
from .get_all import get_all
from .update import update


@group()
def runTemplates():
    """Group allowing solutions run Templates management"""
    pass


list_commands = [add, get, get_all, delete, update]

for _command in list_commands:
    runTemplates.add_command(_command)

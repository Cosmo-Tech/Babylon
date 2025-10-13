from .get import get
from .add import add
from click import group
from .update import update
from .delete import delete
from .get_all import get_all


@group()
def runTemplates():
    """Group allowing solutions run Templates management"""
    pass


list_commands = [add, get, get_all, delete, update]

for _command in list_commands:
    runTemplates.add_command(_command)

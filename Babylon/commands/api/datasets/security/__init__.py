from click import group
from .get import get
from .add import add
from .update import update
from .delete import delete


@group()
def security():
    """Group allowing dataset security management"""
    pass


list_commands = [add, get, update, delete]

for _command in list_commands:
    security.add_command(_command)

from click import group

from .add import add
from .get import get
from .update import update
from .delete import delete
from .get_all import get_all
from .add_default import add_default


@group()
def security():
    """Group allowing scenario security management"""
    pass


list_commands = [add, get, update, delete, get_all, add_default]

for _command in list_commands:
    security.add_command(_command)

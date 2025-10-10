from click import group

from .add import add
from .get import get
from .update import update
from .delete import delete
from .get_all import get_all
from .set_default import set_default


@group()
def security():
    """Group allowing runner security management"""
    pass


list_commands = [add, get, update, delete, get_all, set_default]

for _command in list_commands:
    security.add_command(_command)

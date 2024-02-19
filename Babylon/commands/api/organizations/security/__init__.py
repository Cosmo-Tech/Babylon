from click import group
from .get import get
from .add import add
from .update import update
from .delete import delete
from .get_all import get_all
from .set_default import set_default


@group()
def security():
    """Group allowing organization security management"""
    pass


list_commands = [add, get, update, delete, get_all, set_default]

for _command in list_commands:
    security.add_command(_command)

from click import group

from .add import add
from .delete import delete
from .get import get
from .get_all import get_all
from .set_default import set_default
from .update import update


@group()
def security():
    """Group allowing workspace security management"""
    pass


list_commands = [add, get, update, delete, set_default, get_all]

for _command in list_commands:
    security.add_command(_command)

from click import group
from .get import get
from .add import add
from .update import update
from .delete import delete
from .set_default import set_default
from .get_all import get_all


@group()
def security():
    """Group allowing workspace security management"""
    pass


list_commands = [add, get, update, delete, set_default, get_all]

for _command in list_commands:
    security.add_command(_command)

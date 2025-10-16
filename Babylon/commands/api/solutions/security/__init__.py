from .get import get
from .add import add
from click import group
from .update import update
from .delete import delete
from .get_all import get_all
from .get_users import get_users
from .set_default import set_default


@group()
def security():
    """Group allowing solutions security management"""
    pass


list_commands = [add, get, get_all, get_users, delete, set_default, update]

for _command in list_commands:
    security.add_command(_command)

from click import group
from .get_control_access import get_control_access
from .add_control_access import add_control_access
from .set_default import set_default
from .update_control_access import update_control_access
from .remove_control_access import remove_control_access
from .get_security import get_security
from .get_users import get_users


@group()
def security():
    """Group allowing solutions security management"""
    pass


list_commands = [
    add_control_access, get_control_access, get_security, get_users, remove_control_access, set_default,
    update_control_access
]

for _command in list_commands:
    security.add_command(_command)

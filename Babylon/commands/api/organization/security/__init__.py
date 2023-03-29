from click import group

from .get import get
from .update import update


@group()
def security():
    """Group allowing organization security management"""
    pass


list_commands = [
    update,
    get,
]

for _command in list_commands:
    security.add_command(_command)

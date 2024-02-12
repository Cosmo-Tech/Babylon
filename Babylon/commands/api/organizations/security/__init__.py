from click import group
from .get import get
from .add import add


@group()
def security():
    """Group allowing organization security management"""
    pass


list_commands = [
    add,
    get,
]

for _command in list_commands:
    security.add_command(_command)

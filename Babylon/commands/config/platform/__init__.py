from click import group

from .set_variable import set_variable
from .create import create
from .edit import edit
from .select import select

list_commands = [
    set_variable,
    create,
    edit,
    select,
]


@group()
def platform():
    """Sub-group for platform"""
    pass


for _command in list_commands:
    platform.add_command(_command)

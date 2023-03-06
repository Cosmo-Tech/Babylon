from click import group
from click import pass_context
from click.core import Context

from .remove import remove
from .add import add
from .get_all import get_all

list_commands = [
    remove,
    add,
    get_all,
]


@group()
@pass_context
def member(ctx: Context):
    """Group interacting with Azure Directory Group members"""
    pass


for _command in list_commands:
    member.add_command(_command)

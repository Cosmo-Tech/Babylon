from click import group
from click import pass_context
from click.core import Context

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
@pass_context
def deployment(ctx: Context):
    """Sub-group for deployment"""
    pass


for _command in list_commands:
    deployment.add_command(_command)

from click import group
from click import pass_context
from click.core import Context

from .get_current import get_current
from .create import create
from .delete import delete
from .get import get
from .get_all import get_all
from .user import user

list_groups = [
    user,
]

list_commands = [
    get_current,
    get,
    get_all,
    create,
    delete,
]


@group()
@pass_context
def workspace(ctx: Context):
    """Command group handling PowerBI workspaces"""
    pass


for _command in list_commands:
    workspace.add_command(_command)

for _group in list_groups:
    workspace.add_command(_group)

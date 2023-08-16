from click import group
from click import pass_context
from click.core import Context
from .activate import activate
from .add import add
from .deactivate import deactivate
from .remove import remove

list_commands = [
    remove,
    deactivate,
    activate,
    add,
]


@group()
@pass_context
def plugin(ctx: Context):
    """Subgroup for plugins"""
    pass


for _command in list_commands:
    plugin.add_command(_command)

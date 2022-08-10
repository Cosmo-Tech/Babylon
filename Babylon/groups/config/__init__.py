from click import group
from click import pass_context
from click.core import Context

from .commands import list_commands
from .groups import list_groups
from ...utils.decorators import pass_solution


@group()
@pass_solution
@pass_context
def config(ctx: Context, env):
    """Group made to work on the config"""
    ctx.obj = env.config


for _command in list_commands:
    config.add_command(_command)

for _group in list_groups:
    config.add_command(_group)

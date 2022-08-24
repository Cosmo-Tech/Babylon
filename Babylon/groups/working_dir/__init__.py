from click import group
from click import pass_context

from .commands import list_commands
from .groups import list_groups
from ...utils.decorators import pass_environment


@group()
@pass_environment
@pass_context
def working_dir(ctx, environment):
    """Command group handling working directory information"""
    ctx.obj = environment.working_dir


for _command in list_commands:
    working_dir.add_command(_command)

for _command in list_groups:
    working_dir.add_command(_command)

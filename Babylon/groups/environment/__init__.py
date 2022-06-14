from click import group
from click import pass_context
from .commands import list_commands


@group()
@pass_context
def environment(ctx):
    """Command group handling local environment informations"""
    ctx.obj = dict()
    ctx.obj['group'] = "environment"


for _command in list_commands:
    environment.add_command(_command)

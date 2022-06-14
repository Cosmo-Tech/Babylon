from click import group
from click import pass_context
from .commands import list_commands


@group()
@pass_context
def api(ctx):
    """Group handling communication with the cosmotech API"""
    ctx.obj = dict()
    ctx.obj['group'] = "API"


for _command in list_commands:
    api.add_command(_command)

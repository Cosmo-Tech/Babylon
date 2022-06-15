from click import group
from click import pass_context
from .commands import list_commands


@group()
def api():
    """Group handling communication with the cosmotech API"""
    pass


for _command in list_commands:
    api.add_command(_command)

from click import group

from .commands import list_commands
from .groups import list_groups


@group()
def app_settings():
    """Group initialized from a template"""
    pass


for _command in list_commands:
    app_settings.add_command(_command)

for _group in list_groups:
    app_settings.add_command(_group)

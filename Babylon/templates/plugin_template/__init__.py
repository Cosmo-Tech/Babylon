from click import group

from .commands import list_commands
from .groups import list_groups


@group()
def plugin_template():
    """Plugin `plugin_template` initialized from a template"""
    pass


for _command in list_commands:
    plugin_template.add_command(_command)

for _group in list_groups:
    plugin_template.add_command(_group)

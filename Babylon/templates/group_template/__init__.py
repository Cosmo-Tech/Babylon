from click import group

from .commands import list_commands
from .groups import list_groups


@group()
def group_template():
    """Group initialized from a template"""
    pass


for _command in list_commands:
    group_template.add_command(_command)

for _group in list_groups:
    group_template.add_command(_group)

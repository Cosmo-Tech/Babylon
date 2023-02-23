from click import group

from .commands import list_commands
from .groups import list_groups


@group()
def report():
    """Command group handling PowerBI reports"""
    pass


for _command in list_commands:
    report.add_command(_command)

for _group in list_groups:
    report.add_command(_group)

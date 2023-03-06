from click import group
from click import Group
from click import Command

list_commands: list[Command] = []
list_groups: list[Group] = []


@group()
def group_template():
    """Group initialized from a template"""
    pass


for _command in list_commands:
    group_template.add_command(_command)

for _group in list_groups:
    group_template.add_command(_group)

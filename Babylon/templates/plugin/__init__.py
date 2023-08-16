from click import group
from click import Command
from click import Group

list_commands: list[Command] = []
list_groups: list[Group] = []


@group()
def plugin_template():
    """Plugin `plugin_template` initialized from a template"""
    pass


for _command in list_commands:
    plugin_template.add_command(_command)

for _group in list_groups:
    plugin_template.add_command(_group)

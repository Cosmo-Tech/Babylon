from click import group
from .move import move
from .check import check

list_commands = [move, check]
list_groups = []


@group("resource")
def resource_group():
    """Azure resource group mgmt"""
    pass


for cmd in list_commands:
    resource_group.add_command(cmd)

for grps in list_groups:
    resource_group.add_command(grps)

from click import group

from .member import member
from .get_all import get_all

list_groups = [member]
list_commands = [get_all]


@group()
def group():
    """Group interacting with Azure Directory Groups"""
    pass


for _group in list_groups:
    group.add_command(_group)

for _cmd in list_commands:
    group.add_command(_cmd)
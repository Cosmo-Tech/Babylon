from click import group

from .commands import list_commands
from .groups import list_groups


@group()
def workspace():
    """Sub-group allowing interaction with the organization of the Terraform Cloud API"""
    pass


for _command in list_commands:
    workspace.add_command(_command)

for _group in list_groups:
    workspace.add_command(_group)

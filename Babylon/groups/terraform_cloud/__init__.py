from click import group

from .commands import list_commands
from .groups import list_groups


@group()
def terraform_cloud():
    """Group allowing interactions with the Terraform Cloud API"""
    pass


for _command in list_commands:
    terraform_cloud.add_command(_command)

for _group in list_groups:
    terraform_cloud.add_command(_group)

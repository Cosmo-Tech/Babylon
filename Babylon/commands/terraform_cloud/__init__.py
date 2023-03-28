from click import group

from .workspace import workspace
from .login import login
from .logout import logout

list_groups = [
    workspace,
]

list_commands = [login, logout]


@group()
def terraform_cloud():
    """Group allowing interactions with the Terraform Cloud API"""
    pass


for _group in list_groups:
    terraform_cloud.add_command(_group)

for _command in list_commands:
    terraform_cloud.add_command(_command)
from click import group

from Babylon.utils.environment import Environment
from .workspace import workspace

env = Environment()

list_groups = [
    workspace,
]

list_commands = []


@group()
def terraform_cloud():
    """Group allowing interactions with the Terraform Cloud API"""
    env.check_environ(["BABYLON_SERVICE", "BABYLON_TOKEN", "BABYLON_ORG_NAME"])


for _group in list_groups:
    terraform_cloud.add_command(_group)

for _command in list_commands:
    terraform_cloud.add_command(_command)

from click import group

from .workspace import workspace

list_groups = [
    workspace,
]


@group()
def terraform_cloud():
    """Group allowing interactions with the Terraform Cloud API"""
    pass


for _group in list_groups:
    terraform_cloud.add_command(_group)

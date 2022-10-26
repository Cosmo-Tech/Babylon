from click import group
from click import pass_context
from click.core import Context
from terrasnek.api import TFC

from .commands import list_commands
from .groups import list_groups
from ...utils.decorators import working_dir_requires_yaml_key


@group()
@pass_context
@working_dir_requires_yaml_key("terraform_cloud.yaml", "token", "terraform_token")
@working_dir_requires_yaml_key("terraform_cloud.yaml", "url", "terraform_url")
@working_dir_requires_yaml_key("terraform_cloud.yaml", "organization", "terraform_organization")
def terraform_cloud(ctx: Context, terraform_token: str, terraform_url: str, terraform_organization: str):
    """Group allowing interactions with the Terraform Cloud API"""
    api = TFC(terraform_token, terraform_url)
    api.set_org(terraform_organization)
    ctx.obj = api


for _command in list_commands:
    terraform_cloud.add_command(_command)

for _group in list_groups:
    terraform_cloud.add_command(_group)

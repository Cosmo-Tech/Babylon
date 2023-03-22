import logging

from click import command
from click import option

from ...utils.typing import QueryType
from ...utils.environment import Environment
from ...utils.response import CommandResponse

logger = logging.getLogger("Babylon")


@command()
@option("-u", "--url", "url", help="Terraform cloud API url", type=QueryType(), default="https://app.terraform.io")
@option("-o", "--organization", "organization_name", help="Terraform organization name", prompt=True, type=QueryType())
@option("-t", "--token", "token", help="token", type=QueryType(), prompt=True)
def login(url: str, organization_name: str, token: str) -> CommandResponse:
    """Store terraform cloud login using secrets stored in .secrets.yaml.encrypt"""
    env = Environment()
    env.working_dir.set_encrypted_yaml_key(".secrets.yaml.encrypt", "tfc", {
        "organization": organization_name,
        "token": token,
        "url": url
    })
    logger.info("Successfully updated Terraform Cloud credentials")
    return CommandResponse.success()

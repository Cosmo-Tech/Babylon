import logging

from click import command
from click import option
from click import prompt

from ...utils.typing import QueryType
from ...utils.environment import Environment
from ...utils.response import CommandResponse

logger = logging.getLogger("Babylon")


@command()
@option("-i", "--id", "client_id", help="Client ID", type=QueryType(), prompt=True)
@option("-p", "--secret", "client_secret", help="Client secret", type=QueryType(), prompt=True)
@option("-t", "--tenant", "tenant_id", help="Tenant ID", type=QueryType(), prompt=True)
def login(client_id: str, client_secret: str, tenant_id: str) -> CommandResponse:
    """Login to azure using secrets stored in .secrets.yaml"""
    env = Environment()
    env.working_dir.set_encrypted_yaml_key(".secrets.yaml.encrypt", "azure", {
        "client_secret": client_secret,
        "client_id": client_id,
        "tenant_id": tenant_id
    })
    logger.info("Successfully updated azure credentials")
    return CommandResponse.success()

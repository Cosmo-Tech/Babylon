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
@option("-t", "--tenant", "tenant_id", help="Tenant ID", type=QueryType())
def login(client_id: str, client_secret: str, tenant_id: str) -> CommandResponse:
    """Login to azure using secrets stored in .secrets.yaml"""
    env = Environment()
    tenant_id = tenant_id or env.convert_data_query("%platform%azure_tenant_id")
    if not tenant_id:
        tenant_id = prompt("Tenant ID:")

    env.working_dir.set_yaml_key(".secrets.yaml.encrypt", "azure", {
        "client_secret": client_secret,
        "client_id": client_id,
        "tenant_id": tenant_id
    })
    logger.info("Successfully updated azure credentials")
    return CommandResponse.success()

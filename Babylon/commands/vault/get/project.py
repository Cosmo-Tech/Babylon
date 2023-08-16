import logging

from hvac import Client
from click import Choice, argument, command
from typing import Any
from Babylon.utils.clients import pass_hvac_client
from Babylon.utils.decorators import inject_context_with_resource
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@pass_hvac_client
@argument("resource", type=Choice(['azf', 'powerbi']))
@inject_context_with_resource({
    'api': ['organization_id', 'workspace_key'],
})
def project(
    context: Any,
    hvac_client: Client,
    resource: str,
) -> CommandResponse:
    """
    Get a secret from project scope
    """
    org_id = context['api_organization_id']
    work_key = context['api_workspace_key']
    prefix = f"{env.organization_name}/{env.tenant_id}/projects/{env.context_id}"
    schema = f"{prefix}/{env.environ_id}/{org_id}/{work_key}/{resource}"
    response = hvac_client.read(path=schema)
    if not response:
        logger.info("Secret not found")
        return CommandResponse.fail()
    print(response['data']['secret'])
    return CommandResponse.success()

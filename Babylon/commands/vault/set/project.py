import logging

from typing import Any
from click import Choice, argument, command
from hvac import Client
from Babylon.utils.clients import pass_hvac_client
from Babylon.utils.decorators import inject_context_with_resource, wrapcontext
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse
from Babylon.utils.typing import QueryType

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@pass_hvac_client
@argument("resource", type=Choice(['azf', 'powerbi', 'eventhub', 'func']))
@argument("value", type=QueryType())
@inject_context_with_resource({'api': ['organization_id', 'workspace_key']})
def project(context: Any, hvac_client: Client, resource: str, value: str) -> CommandResponse:
    """
    Set a secret in project scope
    """
    org_id: str = context['api_organization_id']
    work_key: str = context['api_workspace_key']
    d = dict(secret=value)
    prefix = f"{env.organization_name}/{env.tenant_id}/projects/{env.context_id}"
    schema = f"{prefix}/{env.environ_id}/{org_id}/{work_key}/{resource}".lower()
    hvac_client.write(path=schema, **d)
    logger.info("Successfully created")
    return CommandResponse.success()

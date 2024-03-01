import logging

from hvac import Client
from click import Choice, argument, command
from Babylon.utils.clients import pass_hvac_client
<<<<<<< HEAD
from Babylon.utils.decorators import injectcontext, retrieve_state
=======
from Babylon.utils.decorators import inject_context_with_resource, injectcontext
>>>>>>> 53b0a6f8 (add injectcontext)
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@pass_hvac_client
@argument("resource", type=Choice(['azf', 'powerbi', 'eventhub', 'func']))
@argument("value", type=str)
@retrieve_state
def project(state: dict, hvac_client: Client, resource: str, value: str) -> CommandResponse:
    """
    Set a secret in project scope
    """
    org_id: str = state['services']['api']['organization_id']
    work_key: str = state['services']['api']['workspace_key']
    d = dict(secret=value)
    prefix = f"{env.organization_name}/{env.tenant_id}/projects/{env.context_id}"
    schema = f"{prefix}/{env.environ_id}/{org_id}/{work_key}/{resource}".lower()
    hvac_client.write(path=schema, **d)
    logger.info("Successfully created secret hvac in project")
    return CommandResponse.success()

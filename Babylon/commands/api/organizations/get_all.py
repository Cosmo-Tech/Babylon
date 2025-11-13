import jmespath

from logging import getLogger
from typing import Any
from click import command, option, echo, style
from Babylon.utils.decorators import retrieve_state
from Babylon.utils.decorators import injectcontext
from Babylon.utils.response import CommandResponse
from Babylon.utils.decorators import output_to_file
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.environment import Environment
from Babylon.commands.api.organizations.services.organization_api_svc import OrganizationService

logger = getLogger(__name__)
env = Environment()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--filter", "filter", help="Filter response with a jmespath query")
@retrieve_state
def get_all(state: Any, keycloak_token: str, filter: str) -> CommandResponse:
    """
    Get all organizations details
    """
    _org = [""]
    _org.append("Get all organizations details")
    _org.append("")
    echo(style("\n".join(_org), bold=True, fg="green"))
    organization_service = OrganizationService(state=state['services'], keycloak_token=keycloak_token)
    response = organization_service.get_all()
    if response is None:
        return CommandResponse.fail()
    organizations = response.json()
    if len(organizations) and filter:
        organizations = jmespath.search(filter, organizations)
    env.store_state_in_local(state)
    if env.remote:
        env.store_state_in_cloud(state)
    ids = [o["id"] for o in organizations]
    logger.info(f"Retrieved {ids} organizations details")
    return CommandResponse.success(organizations)

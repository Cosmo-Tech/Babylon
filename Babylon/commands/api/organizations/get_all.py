from logging import getLogger
from typing import Any

import jmespath
from click import command, echo, option, style

from Babylon.commands.api.organizations.services.organization_api_svc import OrganizationService
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import injectcontext, output_to_file, retrieve_state
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger(__name__)
env = Environment()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--filter", "filter", help="Filter response with a jmespath query")
@retrieve_state
def get_all(state: Any, config: Any, keycloak_token: str, filter: str) -> CommandResponse:
    """
    Get all organizations details
    """
    _org = [""]
    _org.append("Get all organizations details")
    _org.append("")
    echo(style("\n".join(_org), bold=True, fg="green"))
    services_state = state["services"]["api"]
    organization_service = OrganizationService(state=services_state, config=config, keycloak_token=keycloak_token)
    response = organization_service.get_all()
    if response is None:
        return CommandResponse.fail()
    organizations = response.json()
    if len(organizations) and filter:
        organizations = jmespath.search(filter, organizations)
    ids = [o["id"] for o in organizations]
    logger.info(f"Retrieved {ids} organizations details")
    return CommandResponse.success(organizations)

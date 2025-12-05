from logging import getLogger
from typing import Any

from click import argument, command, echo, style

from Babylon.commands.api.organizations.services.organization_security_svc import OrganizationSecurityService
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
@argument("organization_id", required=True)
@retrieve_state
def get_all(state: Any, config: Any, organization_id: str, keycloak_token: str) -> CommandResponse:
    """
    Get all RBAC access to the organization

    Args:

       ORGANIZATION_ID : The unique identifier of the organization
    """
    _org = [""]
    _org.append("Get all RBAC access to the organization")
    _org.append("")
    echo(style("\n".join(_org), bold=True, fg="green"))
    services_state = state["services"]["api"]
    services_state["organization_id"] = organization_id or services_state["organization_id"]
    service = OrganizationSecurityService(keycloak_token=keycloak_token, state=services_state, config=config)
    logger.info(f"Retrieving all RBAC access to the organization {[services_state['organization_id']]}")
    response = service.get_all()
    if response is None:
        return CommandResponse.fail()
    rbacs = response.json()
    return CommandResponse.success(rbacs)

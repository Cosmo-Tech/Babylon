from logging import getLogger
from typing import Any
from click import command, echo, style, option
from Babylon.commands.api.organizations.services.organization_security_svc import OrganizationSecurityService
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import retrieve_state, injectcontext
from Babylon.utils.decorators import output_to_file
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger(__name__)
env = Environment()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--organization-id", "organization_id", type=str)
@retrieve_state
def get_all(state: Any, organization_id: str, keycloak_token: str) -> CommandResponse:
    """
    Get all RBAC access to the organization
    """
    _org = [""]
    _org.append("Get all RBAC access to the organization")
    _org.append("")
    echo(style("\n".join(_org), bold=True, fg="green"))
    service_state = state["services"]
    service_state["api"]["organization_id"] = organization_id or state["services"]["api"]["organization_id"]
    service = OrganizationSecurityService(keycloak_token=keycloak_token, state=service_state)
    logger.info(f"Retrieving all RBAC access to the organization {[service_state['api']['organization_id']]}")
    response = service.get_all()
    if response is None:
        return CommandResponse.fail()
    rbacs = response.json()
    return CommandResponse.success(rbacs)

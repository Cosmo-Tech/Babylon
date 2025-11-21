from logging import getLogger
from typing import Any

from click import command, echo, option, style

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
@option("--email", "email", type=str, required=True, help="Email valid")
@option("--organization-id", "organization_id", type=str)
@retrieve_state
def get(state: Any, organization_id: str, keycloak_token: str, email: str) -> CommandResponse:
    """
    Get organization user RBAC access
    """
    _org = [""]
    _org.append("Get organization user RBAC access")
    _org.append("")
    echo(style("\n".join(_org), bold=True, fg="green"))
    service_state = state["services"]
    service_state["api"]["organization_id"] = organization_id or state["services"]["api"]["organization_id"]
    service = OrganizationSecurityService(keycloak_token=keycloak_token, state=service_state)
    logger.info(f"Get user {[email]} RBAC access to the organization {[service_state['api']['organization_id']]}")
    response = service.get(id=email)
    if response is None:
        return CommandResponse.fail()
    rbac = response.json()
    return CommandResponse.success(rbac)

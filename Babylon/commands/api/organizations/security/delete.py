import logging

from click import command, echo, option, style

from Babylon.commands.api.organizations.services.organization_security_svc import (
    OrganizationSecurityService,
)
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import injectcontext, output_to_file, retrieve_state
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = logging.getLogger(__name__)
env = Environment()


@command()
@injectcontext()
@pass_keycloak_token()
@output_to_file
@option("--organization-id", "organization_id", type=str)
@option("--email", "email", type=str, required=True, help="Email valid")
@retrieve_state
def delete(state: dict, keycloak_token: str, email: str, organization_id: str) -> CommandResponse:
    """
    Delete organization users RBAC access
    """
    _org = [""]
    _org.append("Delete organization user RBAC access")
    _org.append("")
    echo(style("\n".join(_org), bold=True, fg="green"))
    service_state = state["services"]
    service_state["api"]["organization_id"] = organization_id or service_state["api"]["organization_id"]
    service = OrganizationSecurityService(keycloak_token=keycloak_token, state=service_state)
    logger.info(
        f"Deleting user {[email]} RBAC access from the organization {[service_state['api']['organization_id']]}"
    )
    response = service.delete(id=email)
    if response is None:
        return CommandResponse.fail()
    logger.info(f"User {[email]} RBAC access successfully deleted")
    return CommandResponse.success(response)

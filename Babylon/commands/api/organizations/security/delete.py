import logging

from click import argument, command, echo, option, style

from Babylon.commands.api.organizations.services.organization_security_svc import (
    OrganizationSecurityService,
)
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import injectcontext, output_to_file, retrieve_config_state
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = logging.getLogger(__name__)
env = Environment()


@command()
@injectcontext()
@pass_keycloak_token()
@output_to_file
@argument("organization_id", required=True)
@option("--email", "email", type=str, required=True, help="Email valid")
@retrieve_config_state
def delete(state: dict, config: dict, keycloak_token: str, email: str, organization_id: str) -> CommandResponse:
    """
    Delete organization users RBAC access

    Args:

       ORGANIZATION_ID : The unique identifier of the organization
    """
    _org = [""]
    _org.append("Delete organization user RBAC access")
    _org.append("")
    echo(style("\n".join(_org), bold=True, fg="green"))
    services_state = state["services"]["api"]
    services_state["organization_id"] = organization_id or services_state["organization_id"]
    service = OrganizationSecurityService(keycloak_token=keycloak_token, state=services_state, config=config)
    logger.info(f"Deleting user {[email]} RBAC access from the organization {[services_state['organization_id']]}")
    response = service.delete(id=email)
    if response is None:
        return CommandResponse.fail()
    logger.info(f"User {[email]} RBAC access successfully deleted")
    return CommandResponse.success(response)

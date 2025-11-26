from logging import getLogger
from typing import Any
from click import option, command, echo, style, argument
from Babylon.commands.api.organizations.services.organization_security_svc import OrganizationSecurityService
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import retrieve_config_state, injectcontext
from Babylon.utils.decorators import output_to_file
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger(__name__)
env = Environment()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--email", "email", type=str, required=True, help="Email valid")
@argument("organization_id", required=True)
@retrieve_config_state
def get(state: Any, config: Any, organization_id: str, keycloak_token: str, email: str) -> CommandResponse:
    """
    Get organization user RBAC access

    Args:

       ORGANIZATION_ID : The unique identifier of the organization
    """
    _org = [""]
    _org.append("Get organization user RBAC access")
    _org.append("")
    echo(style("\n".join(_org), bold=True, fg="green"))
    services_state = state["services"]["api"]
    services_state["organization_id"] = organization_id or services_state["organization_id"]
    service = OrganizationSecurityService(keycloak_token=keycloak_token, state=services_state, config=config)
    logger.info(f"Get user {[email]} RBAC access to the organization {[services_state['organization_id']]}")
    response = service.get(id=email)
    if response is None:
        return CommandResponse.fail()
    rbac = response.json()
    return CommandResponse.success(rbac)

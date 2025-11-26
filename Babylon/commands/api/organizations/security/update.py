import json
import logging

from click import command, option, echo, style, argument
from Babylon.utils.decorators import injectcontext
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import output_to_file, retrieve_config_state
from Babylon.commands.api.organizations.services.organization_security_svc import (
    OrganizationSecurityService, )

logger = logging.getLogger(__name__)
env = Environment()


@command()
@injectcontext()
@pass_keycloak_token()
@output_to_file
@option(
    "--role",
    "role",
    type=str,
    required=True,
    help="Role RBAC",
)
@argument("organization_id", required=True)
@option("--email", "email", type=str, required=True, help="Email valid")
@retrieve_config_state
def update(state: dict, config: dict, keycloak_token: str, organization_id: str, email: str,
           role: str) -> CommandResponse:
    """
    Update organization users RBAC access

    Args:

       ORGANIZATION_ID : The unique identifier of the organization
    """
    _org = [""]
    _org.append("Update organization user RBAC access")
    _org.append("")
    echo(style("\n".join(_org), bold=True, fg="green"))
    services_state = state["services"]["api"]
    services_state["organization_id"] = organization_id or services_state["organization_id"]
    details = json.dumps({"id": email, "role": role})
    service = OrganizationSecurityService(keycloak_token=keycloak_token, state=services_state, config=config)
    logger.info(f"[api] Updating user {[email]} RBAC access in the organization {[services_state['organization_id']]}")
    response = service.update(id=email, details=details)
    if response is None:
        return CommandResponse.fail()
    rbacs = response.json()
    logger.info(f"User {[email]} RBAC access successfully updated")
    return CommandResponse.success(rbacs)

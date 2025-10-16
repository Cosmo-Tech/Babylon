import json
import logging

from click import command, option, echo, style
from Babylon.utils.decorators import injectcontext
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import output_to_file, retrieve_state
from Babylon.commands.api.organizations.services.organization_security_svc import (
    OrganizationSecurityService, )

logger = logging.getLogger("Babylon")
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
@option("--organization-id", "organization_id", type=str)
@option("--email", "email", type=str, required=True, help="Email valid")
@retrieve_state
def update(state: dict, keycloak_token: str, organization_id: str, email: str, role: str) -> CommandResponse:
    """
    Update organization users RBAC access
    """
    _org = [""]
    _org.append("Update organization user RBAC access")
    _org.append("")
    echo(style("\n".join(_org), bold=True, fg="green"))
    service_state = state["services"]
    service_state["api"]["organization_id"] = organization_id or state["services"]["api"]["organization_id"]
    details = json.dumps({"id": email, "role": role})
    service = OrganizationSecurityService(keycloak_token=keycloak_token, state=service_state)
    logger.info(
        f"[api] Updating user {[email]} RBAC access in the organization {[service_state['api']['organization_id']]}")
    response = service.update(id=email, details=details)
    if response is None:
        return CommandResponse.fail()
    rbacs = response.json()
    logger.info(json.dumps(rbacs, indent=2))
    logger.info(f"[api] User {[email]} RBAC access successfully updated")
    return CommandResponse.success(rbacs)

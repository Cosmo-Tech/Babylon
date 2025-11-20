import json

from logging import getLogger
from typing import Any
from click import command, option, echo, style
from Babylon.commands.api.organizations.services.organization_security_svc import (
    OrganizationSecurityService, )
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import (
    retrieve_state,
    injectcontext,
)
from Babylon.utils.decorators import output_to_file
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger(__name__)
env = Environment()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--role", "role", type=str, required=True, help="Role RBAC")
@option("--email", "email", type=str, required=True, help="Email valid")
@option("--organization-id", "organization_id", type=str)
@retrieve_state
def add(state: Any, keycloak_token: str, organization_id: str, email: str, role: str = None) -> CommandResponse:
    """
    Add organization users RBAC access
    """
    _org = [""]
    _org.append("Add organization user RBAC access")
    _org.append("")
    echo(style("\n".join(_org), bold=True, fg="green"))
    service_state = state["services"]
    service_state["api"]["organization_id"] = organization_id or state["services"]["api"]["organization_id"]
    service = OrganizationSecurityService(keycloak_token=keycloak_token, state=service_state)
    details = json.dumps(obj={"id": email, "role": role}, indent=2, ensure_ascii=True)
    logger.info(f"Adding user {[email]} RBAC access to the organization {[service_state['api']['organization_id']]}")
    response = service.add(details)
    if response is None:
        return CommandResponse.fail()
    rbacs = response.json()
    logger.info("User RBAC access successfully added")
    return CommandResponse.success(rbacs)

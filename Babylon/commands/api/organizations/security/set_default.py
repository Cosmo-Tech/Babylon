import json

from logging import getLogger
from typing import Any
from click import command, option, echo, style
from Babylon.commands.api.organizations.services.organization_security_svc import OrganizationSecurityService
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import (
    retrieve_state,
    injectcontext,
)
from Babylon.utils.decorators import output_to_file
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option(
    "--role",
    "role",
    type=str,
    required=True,
    help="Role RBAC",
)
@option("--organization-id", "organization_id", type=str)
@retrieve_state
def set_default(
    state: Any,
    keycloak_token: str,
    organization_id: str,
    role: str = None,
) -> CommandResponse:
    """
    Set default RBAC access to the organization
    """
    _org = [""]
    _org.append("Set default RBAC access to the organization")
    _org.append("")
    echo(style("\n".join(_org), bold=True, fg="green"))
    service_state = state["services"]
    service_state["api"]["organization_id"] = organization_id or state["services"]["api"]["organization_id"]
    service = OrganizationSecurityService(keycloak_token=keycloak_token, state=service_state)
    details = json.dumps(obj={"role": role}, indent=2, ensure_ascii=True)
    logger.info(f"[api] Setting default RBAC access to the organization {[service_state['api']['organization_id']]}")
    response = service.set_default(details)
    if response is None:
        return CommandResponse.fail()
    default_security = response.json()
    logger.info(json.dumps(default_security, indent=2))
    logger.info(f"[api] default RBAC access successfully setted with role {[role]}")
    return CommandResponse.success(default_security)

import json
from logging import getLogger
from typing import Any
from click import command, option, echo, style, argument
from Babylon.commands.api.organizations.services.organization_security_svc import OrganizationSecurityService
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import (
    retrieve_config_state,
    injectcontext,
    output_to_file,
)
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger(__name__)
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
@argument("organization_id", required=True)
@retrieve_config_state
def set_default(
    state: Any,
    config: Any,
    keycloak_token: str,
    organization_id: str,
    role: str = None,
) -> CommandResponse:
    """
    Set default RBAC access to the organization

    Args:

       ORGANIZATION_ID : The unique identifier of the organization
    """
    _org = [""]
    _org.append("Set default RBAC access to the organization")
    _org.append("")
    echo(style("\n".join(_org), bold=True, fg="green"))
    services_state = state["services"]["api"]
    services_state["organization_id"] = organization_id or services_state["organization_id"]
    service = OrganizationSecurityService(keycloak_token=keycloak_token, state=services_state, config=config)
    details = json.dumps(obj={"role": role}, indent=2, ensure_ascii=True)
    logger.info(f"Setting default RBAC access to the organization {[services_state['organization_id']]}")
    response = service.set_default(details)
    if response is None:
        return CommandResponse.fail()
    default_security = response.json()
    logger.info(f"Default RBAC access successfully set with role {[role]}")
    return CommandResponse.success(default_security)

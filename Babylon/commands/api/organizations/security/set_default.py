import json
from logging import getLogger
from typing import Any
from click import command
from click import option
from Babylon.commands.api.organizations.services.security import OrganizationSecurityService
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import (
    retrieve_state,
    injectcontext,
)
from Babylon.utils.decorators import output_to_file
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@timing_decorator
@output_to_file
@pass_azure_token("csm_api")
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
    azure_token: str,
    organization_id: str,
    role: str = None,
) -> CommandResponse:
    """
    Set default RBAC access to organization
    """
    service_state = state["services"]
    service_state["api"]["organization_id"] = organization_id or state["services"]["api"]["organization_id"]
    service = OrganizationSecurityService(azure_token=azure_token, state=service_state)
    details = json.dumps(obj={"role": role}, indent=2, ensure_ascii=True)
    response = service.set_default(details)
    default_security = response.json()
    if response is None:
        return CommandResponse.fail()
    return CommandResponse.success(default_security, verbose=True)

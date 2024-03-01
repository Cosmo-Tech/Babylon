import json
from logging import getLogger
from typing import Any
from click import command
from click import option
from Babylon.commands.api.organizations.services.security import (
    OrganizationSecurityService, )
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
@option("--email", "email", type=str, required=True, help="Email valid")
@retrieve_state
def add(state: Any, azure_token: str, email: str, role: str = None) -> CommandResponse:
    """
    Add organization users RBAC access
    """
    service_state = state["services"]
    service = OrganizationSecurityService(azure_token=azure_token, state=service_state)
    details = json.dumps(obj={"id": email, "role": role}, indent=2, ensure_ascii=True)
    response = service.add(details)
    rbacs = response.json()
    return CommandResponse.success(rbacs, verbose=True)

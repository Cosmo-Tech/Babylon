import json
import logging

from click import argument, command, option
from Babylon.utils.decorators import injectcontext
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import output_to_file, retrieve_state
from Babylon.commands.api.organizations.services.security import (
    OrganizationSecurityService, )

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@pass_azure_token("csm_api")
@output_to_file
@option(
    "--role",
    "role",
    type=str,
    required=True,
    help="Role RBAC",
)
@option("--email", "email", type=str, required=True, help="Email valid")
@argument("identity_id", type=str)
@retrieve_state
def update(state: dict, azure_token: str, identity_id: str, email: str, role: str) -> CommandResponse:
    """
    Update organization users RBAC access
    """
    service_state = state["services"]
    details = json.dumps({"id": email, "role": role})
    service = OrganizationSecurityService(azure_token=azure_token, state=service_state)
    response = service.update(id=identity_id, details=details)
    rbacs = response.json()
    return CommandResponse.success(rbacs, verbose=True)
